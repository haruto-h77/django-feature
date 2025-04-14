from django.urls import path
from . import views

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
    # 関数ビュー
    # path('login', views.Login, name='Login'),
    # path('', views.home, name='home'),
    # path('new', views.new, name='new'),
    # path('edit/<int:pk>', views.edit, name='edit'),
]
