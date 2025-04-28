from django import forms
from .models import Schedule


class BS4ScheduleForm(forms.ModelForm):
    """Bootstrapに対応するためのModelForm"""

    class Meta:
        model = Schedule
        fields = ('summary', 'description', 'start_datetime', 'end_datetime','reminder_enabled')

        widgets = {
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            },
            format='%Y-%m-%dT%H:%M',
            ),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            },
            format='%Y-%m-%dT%H:%M',
            
            ),
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.start_datetime:
            self.fields['start_datetime'].widget.attrs['class'] = 'form-control'


    # 各フィールドに対してのバリデーション確認（HTMLフォームの場合）
    def clean(self):
        cleaned_data = super().clean()
        summary = cleaned_data.get('summary')
        description = cleaned_data.get('description')
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')


        # summaryの文字数チェック
        if summary and len(summary) > 50:
            self.add_error('summary', '1文字以上、50文字以内で入力してください')

        # descriptionの文字数チェック
        if description and len(description) > 200:
            self.add_error('description', '200文字以内で入力してください')

        # どれかの日時が未入力の場合
        if None in (start_datetime, end_datetime):
            raise forms.ValidationError('すべての日時を入力してください。')

        # 終了日より開始日の方が後の日付に設定されていた場合
        if end_datetime < start_datetime:
            self.add_error('end_datetime','終了日時が開始日時より前に設定されています')
        
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
        fields = ('summary', 'description', 'start_datetime', 'end_datetime','reminder_enabled')
        # 入力ウィジェットのカスタム
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'summary': forms.TextInput(attrs={'class': 'form-control'}),
            'reminder_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        # 必要に応じてラベルも変更可能
        labels = {
            'summary': '概要',
            'description': '詳細',
            'start_datetime': '開始日時',
            'end_datetime': '終了日時',
            'reminder_enabled': 'リマインダーを有効にする',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        summary = cleaned_data.get('summary')
        description = cleaned_data.get('description')
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        # summaryの文字数チェック
        if summary and len(summary) > 50:
            self.add_error('summary', '1文字以上、50文字以内で入力してください')

        # descriptionの文字数チェック
        if description and len(description) > 200:
            self.add_error('description', '200文字以内で入力してください')

        # 時刻と日付の入力チェック
        if None in (start_datetime, end_datetime):
            raise forms.ValidationError('日付・開始時刻・終了時刻をすべて入力してください。')

        # 時間の整合性チェック（同日内）
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error('end_datetime', '終了日時が開始日時よりも前に設定されています')

        return cleaned_data
