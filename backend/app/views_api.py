# views_api.py など別ファイルで切り出すのもおすすめ

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Schedule
from .serializers import ScheduleSerializer
from django.shortcuts import get_object_or_404
from datetime import date, timedelta, datetime
import calendar
from rest_framework.permissions import AllowAny

# 一覧 + 新規作成
class ScheduleListCreateAPIView(APIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    def get(self, request):
        # 全てのスケジュールを取得
        schedules = Schedule.objects.all()
        # 複数のスケジュールを1つ1つJSON形式に変更（many=true）
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    def post(self, request):
        # 入力データから新しいスケジュールを作る準備
        serializer = ScheduleSerializer(data=request.data)
        # バリデーション確認
        if serializer.is_valid():
            # データベースに保存
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 詳細取得 + 更新 + 削除
class ScheduleDetailAPIView(APIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    # 指定された主キーに一致するScheduleを取得するヘルパー関数
    def get_object(self, pk):
        return get_object_or_404(Schedule, pk=pk)

    # 詳細取得
    def get(self, request, pk):
        # 指定された主キーに一致するスケジュールを取得
        schedule = self.get_object(pk)
        # JSON形式に変換
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)

    # 更新
    def put(self, request, pk):
        # 指定された主キーに一致するスケジュールを取得
        schedule = self.get_object(pk)
        # JSON形式に変換して更新する
        serializer = ScheduleSerializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 削除
    def delete(self, request, pk):
        # 指定された主キーに一致するスケジュールを取得
        schedule = self.get_object(pk)
        # データベースから削除
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# 月毎のカレンダーを取得する
class MonthlyCalendarAPI(APIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    def get(self, request):
        # クエリパラメータから年と月を取得
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))

        # 月の最初の日と月曜日始まりのカレンダー
        first_day = date(year, month, 1)
        start_day = first_day - timedelta(days=first_day.weekday())
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        end_day = last_day + timedelta(days=6 - last_day.weekday())

        # スケジュールをまとめて取得
        schedules = Schedule.objects.filter(date__range=(start_day, end_day))
        schedule_map = {}
        for schedule in schedules:
            key = schedule.date.isoformat()
            schedule_map.setdefault(key, []).append(schedule)

        # カレンダー構造を生成
        current_day = start_day
        weeks = []
        while current_day <= end_day:
            week = []
            for _ in range(7):
                day_str = current_day.isoformat()
                day_schedules = schedule_map.get(day_str, [])
                week.append({
                    'date': day_str,
                    'schedules': ScheduleSerializer(day_schedules, many=True).data
                })
                current_day += timedelta(days=1)
            weeks.append(week)

        return Response({
            'year': year,
            'month': month,
            'weeks': weeks
        })

# 週ごとのカレンダーを取得する
class WeeklyCalendarAPI(APIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    def get(self, request):
        # クエリパラメータから日付を取得
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
        day = int(request.GET.get('day'))

        target_date = datetime(year, month, day).date()
        start_of_week = target_date - timedelta(days=target_date.weekday())  # 月曜始まり
        week = []

        # 7日分のスケジュールを取得
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            schedules = Schedule.objects.filter(date=current_day)
            serialized_schedules = ScheduleSerializer(schedules, many=True).data

            # カレンダー構造を生成
            week.append({
                'date': current_day.isoformat(),
                'schedules': serialized_schedules,
            })

        return Response({
            'year': year,
            'month': month,
            'day': day,
            'week': week
        })
