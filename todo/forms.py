###
# imports
###
# フォーム
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.forms import AuthenticationForm
# モデル
from django.contrib.auth.models import User
from .models import Todo
# timezone
from django.utils import timezone

###
# ログインフォーム
class LoginForm(AuthenticationForm):
    username = forms.CharField(label='ユーザー名', max_length=50)
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput())
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)
       # それぞれのフォームに対してクラスを付与する
       self.fields['username'].widget.attrs['class'] = 'form-control mb-3'
       self.fields['password'].widget.attrs['class'] = 'form-control mb-3'

###
# ユーザーの新規登録用
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control mb-3"

###
# Todoフォーム
class TodoForm(forms.ModelForm):
    # 完了日フィールド（登録時）
    is_finished = forms.BooleanField(required=False,label="完了")
    class Meta:
        model = Todo
        # どのフィールドを使用するか
        fields = ('item_name','user','expire_date','is_finished','finished_date')
        # フィールドに対するラベル
        labels = {
            'item_name': '項目名',
            'user': '担当者',
            'expire_date': '期限日',
        }
        # 基本的なバリデーション
        error_messages = {
            "item_name": {
                "required": "項目名が入力されていません",
            },
            "user": {
                "required": "担当者名が入力されていません",
            },
            "expire_date": {
                "required": "期限日が入力されていません",
            },
        }
        # ウィジェット
        widgets = {
            'expire_date': forms.DateInput(attrs={"type":"date"})
        }
    # 登録時および更新時、初期設定
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finished_date'].widget = forms.HiddenInput()
        for field in self.fields:
            if field != "is_finished":
                self.fields[field].widget.attrs["class"] = "form-control"
    # 項目名に対するバリデーション
    # 100文字以上になっている場合はエラー
    def clean_item_name(self):
        item_name = self.cleaned_data.get('item_name')
        if len(item_name) >= 100:
            self.add_error('item_name', '項目名は100文字以内で入力してください')
        return item_name
    # 期限日に対するバリデーション
    # 形式に合わないデータであればエラー
    def clean_expire_date(self):
        expire_date = self.cleaned_data.get('expire_date')
        try:
            expire_date.strftime('%Y/%m/%d %H:%M:%S')
        except:
            if expire_date is None:
                self.add_error('expire_date', '期限日が入力されていません')
            else:
                self.add_error('expire_date', '日付の形式で入力してください')
        return expire_date
    # 完了日に対する処理
    # チェックが入っていなければ、何もなし。チェックが入っていれば、本日の日付を格納する
    def clean(self):
        cleaned_data = super().clean()
        is_finished = cleaned_data.get('is_finished')
        if is_finished:
            cleaned_data['finished_date'] = timezone.now()
        else:
            cleaned_data['finished_date'] = None
        return cleaned_data

###
# 関数ビュー
###
# ログインフォーム
# class LoginForm(forms.Form):
#     username = forms.CharField(label='ユーザー名', max_length=50)
#     password = forms.CharField(label='パスワード', widget=forms.PasswordInput())
#     def __init__(self,*args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for field in self.fields:
#             self.fields[field].widget.attrs["class"] = "form-control mb-3"
