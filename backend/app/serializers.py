from rest_framework import serializers
from .models import Schedule

# モデル　↔︎　JSON　に変換するクラス
class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'
    
    # JSON形式の場合はserializers.pyでバリデーションを行う（validate_fieldname で 自動的にfieldnameが取れるらしい）
    # タイトル
    def validate_summary(self, value):
        if len(value) > 50:
            raise serializers.ValidationError('1文字以上、50文字以内で入力してください')
        return value
    
    # 内容
    def validate_description(self, value):
        if len(value) > 200:
            raise serializers.ValidationError("200文字以内で入力してください")
        return value
    
    # 時間関連
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if None in (start_date, end_date, start_time, end_time):
            raise serializers.ValidationError('すべての日時を入力してください。')

        if end_date < start_date:
            raise serializers.ValidationError('終了日が開始日より前に設定されています。')

        if start_date == end_date and end_time <= start_time:
            raise serializers.ValidationError('終了時間が開始時間よりも前に設定されています。')

        return data
