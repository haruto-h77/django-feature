from django import forms
from .models import Schedule


class BS4ScheduleForm(forms.ModelForm):
    """Bootstrapに対応するためのModelForm"""

    class Meta:
        model = Schedule
        fields = ('summary', 'description', 'start_date', 'end_date', 'start_time', 'end_time')

        widgets = {
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'readonly': 'readonly',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'start_time': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'end_time': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # start_dateをreadonlyに設定して変更不可にする
        if self.instance and self.instance.start_date:
            self.fields['start_date'].widget.attrs['readonly'] = 'readonly'
            self.fields['start_date'].widget.attrs['class'] = 'form-control'
            self.fields['start_date'].disabled = True  # disabledでフォーム送信時に値を送信しないようにする

    # 各フィールドに対してのバリデーション確認
    def clean(self):
        cleaned_data = super().clean()
        summary = cleaned_data.get('summary')
        description = cleaned_data.get('description')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # summaryの文字数チェック
        if summary and len(summary) > 50:
            self.add_error('summary', '1文字以上、50文字以内で入力してください')

        # descriptionの文字数チェック
        if description and len(description) > 200:
            self.add_error('description', '200文字以内で入力してください')

        # どれかの日時が未入力の場合
        if None in (start_date, end_date, start_time, end_time):
            raise forms.ValidationError('すべての日時を入力してください。')

        # 終了日より開始日の方が後の日付に設定されていた場合
        if end_date < start_date:
            self.add_error('end_date','終了日が開始日より前に設定されています')
        
        if start_date == end_date:
            # 終了時間と開始時間が同じまたは、開始時間のほうが後に設定されている場合
            if end_time <= start_time:
                self.add_error('end_time', '終了時間が開始時間よりも前に設定されています')
        
        return cleaned_data



class SimpleScheduleForm(forms.ModelForm):
    """シンプルなスケジュール登録用フォーム"""

    class Meta:
        model = Schedule
        fields = ('summary', 'date',)
        widgets = {
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'date': forms.HiddenInput,
        }
        

class ScheduleDetailForm(forms.ModelForm):
    """スケジュール詳細画面用のフォーム"""

    class Meta:
        model = Schedule
        # DBで使うテーブル名を指定
        fields = ('summary', 'description', 'start_time', 'end_time', 'date')
        # 入力ウィジェットのカスタム
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'summary': forms.TextInput(attrs={'class': 'form-control'}),
        }
        # 必要に応じてラベルも変更可能
        labels = {
            'summary': '概要',
            'description': '詳細',
            'start_time': '開始時刻',
            'end_time': '終了時刻',
            'date': '日付',
        }

    def clean(self):
        cleaned_data = super().clean()
        summary = cleaned_data.get('summary')
        description = cleaned_data.get('description')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # summaryの文字数チェック
        if summary and len(summary) > 50:
            self.add_error('summary', '1文字以上、50文字以内で入力してください')

        # descriptionの文字数チェック
        if description and len(description) > 200:
            self.add_error('description', '200文字以内で入力してください')

        # 時刻と日付の入力チェック
        if None in (date, start_time, end_time):
            raise forms.ValidationError('日付・開始時刻・終了時刻をすべて入力してください。')

        # 時間の整合性チェック（同日内）
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', '終了時間が開始時間よりも前に設定されています')

        return cleaned_data
