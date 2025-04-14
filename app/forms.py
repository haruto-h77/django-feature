from django import forms
from .models import Schedule


class BS4ScheduleForm(forms.ModelForm):
    """Bootstrapに対応するためのModelForm"""

    class Meta:
        model = Schedule
        fields = ('summary', 'description', 'start_time', 'end_time')
        widgets = {
            'summary': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
            }),
            'start_time': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'end_time': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }

    def clean_end_time(self):
        start_time = self.cleaned_data['start_time']
        end_time = self.cleaned_data['end_time']
        if end_time <= start_time:
            raise forms.ValidationError(
                '終了時間は、開始時間よりも後にしてください'
            )
        return end_time


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
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        # 必要に応じてラベルも変更可能
        labels = {
            'summary': '概要',
            'description': '詳細',
            'start_time': '開始時刻',
            'end_time': '終了時刻',
            'date': '日付',
        }
        
    # # 必要であれば clean_end_time のようなバリデーションも追加
    # def clean_end_time(self):
    #     start_time = self.cleaned_data.get('start_time')
    #     end_time = self.cleaned_data.get('end_time')
    #     # start_time や end_time が取得できない場合も考慮
    #     if start_time and end_time and end_time <= start_time:
    #         raise forms.ValidationError(
    #             '終了時間は、開始時間よりも後にしてください'
    #         )
    #     return end_time
    