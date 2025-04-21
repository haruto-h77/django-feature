from django.urls import path
from . import views
from .views_api import TodoListCreateAPI, TodoDetailUpdateDeleteAPI, TodoCompleteAPI

urlpatterns = [
    # クラスビュー
    path('', views.TodoList.as_view(), name='list'),
    path('login', views.Login.as_view(), name="Login"),
    path("logout",views.Logout.as_view(),name="Logout"),
    path('new', views.TodoCreateView.as_view(), name='new'),
    path('edit/<int:pk>', views.TodoUpdateView.as_view(), name='edit'),
    path('complete', views.TodoCompleteView.as_view(), name='complete'),
    path('delete', views.TodoDeleteView.as_view(), name='delete'),
    path('register', views.UserCreateView.as_view(), name='register'),
    # APIビュー
    path('api/todos/', TodoListCreateAPI.as_view(), name='todo-list-create'),
    path('api/todos/<int:pk>/', TodoDetailUpdateDeleteAPI.as_view(), name='todo-detail-update-delete'),
    path('api/todos/<int:pk>/complete/', TodoCompleteAPI.as_view(), name='todo-complete'),
    # 関数ビュー
    # path('login', views.Login, name='Login'),
    # path('', views.home, name='home'),
    # path('new', views.new, name='new'),
    # path('edit/<int:pk>', views.edit, name='edit'),
]
