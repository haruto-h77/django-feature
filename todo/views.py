###
# imports
###
# ショートカット
from django.shortcuts import render,redirect,get_object_or_404
# クラスビュー
from django.views.generic import ListView,CreateView,UpdateView
from django.contrib.auth.views import LoginView,LogoutView
from django.contrib.auth.forms import UserCreationForm
# フォーム関連
from django import forms
from .forms import LoginForm,TodoForm,CustomUserCreationForm
# ログイン・ログアウト処理に利用
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
# リダイレクト、レスポンス、戻る処理
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.urls import reverse_lazy
# モデル関連
from django.contrib.auth.models import User
from .models import Todo
from django.db.models import Q
from django.utils import timezone

###
# クラスビュー
###
#会員登録ページに関する処理
class UserCreateView(CreateView):
    template_name = 'todo/login.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('Login')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['crud'] = '新規登録' # 画面に渡すパラメータにセット
        return context
# ログイン
class Login(LoginView):
    template_name = 'todo/login.html'
    form_class = LoginForm
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['crud'] = 'ログイン' # 画面に渡すパラメータにセット
        return context
# ログアウト
class Logout(LoginRequiredMixin, LogoutView):
    template_name = 'todo/login.html'
# 一覧画面
class TodoList(LoginRequiredMixin, ListView):
    # Todoテーブルより呼び出す
    model = Todo
    # レコード情報をテンプレートに渡すオブジェクト
    context_object_name = "todos"
    #テンプレートファイル連携
    template_name = "todo_list.html"
    # Todoの一覧をユーザー、検索文字でフィルタして取得する
    def get_queryset(self):
        search_param = self.request.GET.get('search') # 検索文字の取得
        if search_param is None: # 検索文字がない場合
            query_result = self.model.objects.filter(user=self.request.user) # ログインユーザーでフィルタ
        else: # 検索文字がある場合
            query_result = self.model.objects.filter( \
                Q(item_name__icontains=search_param) | Q(user__username__icontains=search_param), \
                user=self.request.user)
        return query_result # 結果を返す
###
# 新規作成画面
class TodoCreateView(LoginRequiredMixin, CreateView):
    # Todo
    model = Todo
    # フォームの設定
    form_class = TodoForm
    # ページの設定
    template_name = "todo/edit.html"
    # 新規登録成功時のURL
    success_url = "/"
    # 登録画面として表示する
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['crud'] = '登録' # 画面に渡すパラメータにセット
        return context
    # 保存前にフォームのデータを変更する
    def form_valid(self, form):
        todo_form = form.save(commit=False)
        todo_form.registration_date = timezone.now() # 登録日を本日にセット
        todo_form.save() # 保存する
        return redirect('/')
###
# 更新画面
class TodoUpdateView(LoginRequiredMixin, UpdateView):
    # Todo
    model = Todo
    # フォームの設定
    form_class = TodoForm
    # ページの設定
    template_name = "todo/edit.html"
    # 新規登録成功時のURL
    success_url = "../"
    # フォームで表示するときの完了チェック
    is_finished = True
    # 編集画面として表示する
    # 編集する予定のTodoを取得して、完了日が入力されているかチェックする
    def get_object(self):
        query_result = Todo.objects.get(pk=self.kwargs["pk"]) # データを取得する
        if query_result.finished_date is None:
            self.is_finished = False
        return query_result
    # フォームの完了日のvalueを編集する
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['is_finished'] = forms.BooleanField(label='完了',initial=self.is_finished, required=False)
        context['crud'] = '編集'
        return context
###
# 削除処理　*POSTのみ
class TodoDeleteView(LoginRequiredMixin, UpdateView):
    # Todo
    model = Todo
    # フィールドの指定
    fields = ('is_deleted', )
    # 削除処理成功時のURL
    success_url = "/"
    # 削除対象であり、ログイン中のユーザーのIDのTodoを取得
    def get_object(self):
        return get_object_or_404(Todo, pk=self.request.POST["id"], user=self.request.user)
    # 削除フィールドを更新する
    def form_valid(self, form):
        todo_form = form.save(commit=False)
        todo_form.is_deleted = True # 削除処理
        todo_form.save() # 保存する
        return redirect('/')
###
# 完了処理　*POSTのみ
class TodoCompleteView(LoginRequiredMixin, UpdateView):
    # Todo
    model = Todo
    # フィールドの指定
    fields = ('finished_date', )
    # 完了処理成功時のURL
    success_url = "/"
    # 完了対象であり、ログイン中のユーザーのIDのTodoを取得
    def get_object(self):
        return get_object_or_404(Todo, pk=self.request.POST["id"], user=self.request.user)
    # 完了日フィールドを更新する
    def form_valid(self, form):
        todo_form = form.save(commit=False)
        todo_form.finished_date = timezone.now() # 削除処理
        todo_form.save() # 保存する
        return redirect('/')
###
# 関数ビュー
###
# 一覧画面
# @login_required
# def home(request):
#     search = request.GET.get('search')
#     if search is None:
#         todos = Todo.objects.filter(user=request.user)
#         params = {"todos":todos,'CRUD':'一覧'}
#         return render(request, 'todo/todo_list.html', params)
#     todos = Todo.objects.filter(Q(item_name__icontains=search)|Q(user__username__icontains=search),user=request.user)
#     params = {"todos":todos,"search":search}
#     return render(request, 'todo/todo_list.html', params)

# 新規登録画面
# @login_required
# def new(request):
#     if request.method == "POST":
#         form = TodoForm(request.POST)
#         if form.is_valid():
#             todo = form.save(commit=False)
#             todo.registration_date = timezone.now()
#             todo.save()
#             return redirect('/')
#     else:
#         form = TodoForm()
#         form.fields['is_finished'] = forms.BooleanField(label='完了',initial=False, required=False)
#     return render(request, 'todo/edit.html', {'CRUD':'登録','form': form})

# ログイン時のみ、編集画面を表示する
# @login_required
# def edit(request, pk):
#     todo = get_object_or_404(Todo, pk=pk)
#     if request.method == "POST":
#         form = TodoForm(request.POST, instance=todo)
#         if form.is_valid():
#             todo = form.save(commit=False)
#             todo.save()
#             return redirect('edit', pk=todo.pk)
#     else:
#         form = TodoForm(instance=todo)
#         is_finished = True
#         if todo.finished_date is None:
#             is_finished = False
#         form.fields['is_finished'] = forms.BooleanField(label='完了',initial=is_finished, required=False)
#     params = {"form":form,'CRUD':'編集'}
#     print(request.user)
#     return render(request, 'todo/edit.html', params)

# ログイン時のみ、削除処理を行う
# @login_required
# def delete(request):
#     id = request.POST.get('id')
#     todo = Todo.objects.get(pk=id)
#     todo.is_deleted = 1
#     todo.save()
#     return redirect('/')

# ログイン時のみ、完了処理を行う
# @login_required
# def complete(request):
#     id = request.POST.get('id')
#     print(id)
#     todo = Todo.objects.get(pk=id)
#     todo.finished_date = timezone.now()
#     todo.save()
#     return redirect('/')

# ログイン画面
# def Login(request):
#     if request.user.is_authenticated:
#         return redirect('/')
#     params = {'message': '', 'form': None}
#     # POST通信だった場合
#     if request.method == 'POST':
#         # POSTされたフォームを取得する
#         form = LoginForm(request.POST)
#         # バリデーションを行う
#         if form.is_valid():
#             pass
#         else:
#             params['form'] = form
#             return render(request, 'todo/login.html', params)
#         # idとpasswordを取得して認証を行う
#         ID = request.POST.get('username')
#         Pass = request.POST.get('password')
#         # 認証チェック
#         user = authenticate(username=ID, password=Pass)
#         # 認証が通った場合
#         if user:
#             login(request,user)
#             return HttpResponseRedirect(reverse('list'))
#         else:
#             # フォームを表示する
#             params['form'] = form
#             params['message'] = 'IDかパスワードに誤りがあります'
#             # ログイン画面に移行
#             return render(request, 'todo/login.html',params)
#     # GET通信だった場合
#     else:
#         params = {'message': '', 'form': None}
#         # フォームを表示する
#         params['form'] = LoginForm()
#         # ログイン画面に移行
#         return render(request, 'todo/login.html',params)

#ログアウト
# @login_required
# def Logout(request):
#     logout(request)
#     # ログイン画面遷移
#     return HttpResponseRedirect(reverse('Login'))
