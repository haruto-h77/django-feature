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
        fields = ('item_name','description','user','expire_datetime','is_finished','finished_date')
        # フィールドに対するラベル
        labels = {
            'item_name': '項目名',
            'description': '概要',
            'user': '担当者',
            'expire_datetime': '期限日時',
            'is_finished': '完了',
            'expire_datetime': '期限日時',
        }
        # 基本的なバリデーション
        error_messages = {
            "item_name": {
                "required": "項目名が入力されていません",
            },
            "user": {
                "required": "担当者名が入力されていません",
            },
            "expire_datetime": {
                "required": "期限日時が入力されていません",
            },
        }
        # ウィジェット
        widgets = {
            'expire_datetime': forms.DateTimeInput(attrs={"type":"datetime-local"}),
        }
    # 登録時および更新時、初期設定
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['finished_date'].widget = forms.HiddenInput()
        for field in self.fields:
            if field != "is_finished":
                self.fields[field].widget.attrs["class"] = "form-control"
    # 項目名に対するバリデーション
    # item_nameの文字数チェック
    def clean_item_name(self):
        item_name = self.cleaned_data.get('item_name')
        if len(item_name) > 50:
            self.add_error('item_name', '1文字以上、50文字以内で入力してください')
        return item_name
    # descriptionの文字数チェック
    def clean_description(self):
        description = self.cleaned_data.get("description")
        if len(description) > 200:
            self.add_error('description', '200文字以内で入力してください')
            return description
    # 期限日に対するバリデーション
    # 形式に合わないデータであればエラー
    def clean_expire_datetime(self):
        expire_datetime = self.cleaned_data.get('expire_datetime')
        try:
            expire_datetime.strftime('%Y/%m/%d %H:%M:%S')
        except:
            if expire_datetime is None:
                self.add_error('expire_datetime', '期限日時が入力されていません')
            else:
                self.add_error('expire_datetime', '日付の形式で入力してください')
        return expire_datetime
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
