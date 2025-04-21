from django.urls import path
from . import views
from .views_api import ScheduleListCreateAPIView, ScheduleDetailAPIView, MonthlyCalendarAPI, WeeklyCalendarAPI
from django.urls import path

app_name = 'app'

urlpatterns = [    
    # 週間ごとのスケジュール 'week_with_schedule'
    path('week_with_schedule/', views.WeekWithScheduleCalendar.as_view(), name='week_with_schedule'),
    path(
        'week_with_schedule/<int:year>/<int:month>/<int:day>/',
        views.WeekWithScheduleCalendar.as_view(),
        name='week_with_schedule'
    ),
    # 月間ごとのスケジュール 'month_with_schedule'
    path(
        'month_with_schedule/',
        views.MonthWithScheduleCalendar.as_view(), name='month_with_schedule'
    ),
    path(
        'month_with_schedule/<int:year>/<int:month>/',
        views.MonthWithScheduleCalendar.as_view(), name='month_with_schedule'
    ),
    # カレンダーに予定を設定する　'mycalendar'
    path('mycalendar/', views.MyCalendar.as_view(), name='mycalendar'),
    path(
        'mycalendar/<int:year>/<int:month>/<int:day>/', views.MyCalendar.as_view(), name='mycalendar'
    ),
    # 予定の詳細画面表示
    path('dayDetail/<int:year>/<int:month>/<int:day>/<int:pk>/', views.DayDetailCalendar.as_view(), name='dayDetail'),
    # 予定の編集画面表示
    path('day/<int:year>/<int:month>/<int:day>/<int:pk>/', views.DayCalendar.as_view(), name='day'),
    # 予定の編集
    path('schedule/edit/<int:pk>/', views.schedule_edit, name='schedule_edit'),
    # 予定の削除
    path('schedule/delete/<int:pk>/', views.schedule_delete, name='schedule_delete'),
    # APIエンドポイント
    path('api/schedules/', ScheduleListCreateAPIView.as_view(), name='schedule-list-create'),
    path('api/schedules/<int:pk>/', ScheduleDetailAPIView.as_view(), name='schedule-detail'),
    path('api/calendar/monthly/', MonthlyCalendarAPI.as_view(), name='monthly-calendar-api'),
    path('api/calendar/weekly/', WeeklyCalendarAPI.as_view(), name='weekly-calendar-api'),
]
