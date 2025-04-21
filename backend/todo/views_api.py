from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Todo
from backend.app.models import Schedule
from backend.linker.models import ScheduleTodoLink
from .serializers import TodoSerializer
from rest_framework.permissions import AllowAny

# Todo一覧取得（GET）、作成（POST）
class TodoListCreateAPI(generics.ListCreateAPIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）    
    serializer_class = TodoSerializer

    def get_queryset(self):
        search_param = self.request.query_params.get('search')
        queryset = Todo.objects.filter(user=self.request.user, is_deleted=False)
        if search_param:
            queryset = queryset.filter(
                Q(item_name__icontains=search_param) | Q(user__username__icontains=search_param)
            )
        return queryset.order_by('finished_date', 'expire_datetime', 'registration_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, registration_date=timezone.now())

# Todo詳細取得（GET）、更新（PUT）、削除（DELETE）
class TodoDetailUpdateDeleteAPI(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    serializer_class = TodoSerializer

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

# Todo完了処理（POST）
class TodoCompleteAPI(APIView):
    permission_classes = [AllowAny]  # 誰でもOK（テスト時のみ）
    def post(self, request, pk):
        todo = get_object_or_404(Todo, pk=pk, user=request.user)
        todo.finished_date = timezone.now()
        todo.save()

        # 関連するスケジュールの完了フラグも更新
        linked_schedules = ScheduleTodoLink.objects.filter(todo=todo)
        for link in linked_schedules:
            schedule = link.schedule
            schedule.is_completed = True
            schedule.save()

        return Response({'message': '完了しました'}, status=status.HTTP_200_OK)
