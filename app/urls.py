from django.urls import path
from . import views

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

    # 予定の詳細表示
    path('day/<int:year>/<int:month>/<int:day>/<int:pk>/', views.DayCalendar.as_view(), name='day'),
    # 予定の編集
    path('schedule/edit/<int:pk>/', views.schedule_edit, name='schedule_edit'),
    # 予定の削除
    path('schedule/delete/<int:pk>/', views.schedule_delete, name='schedule_delete'),
]
