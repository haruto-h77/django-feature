import datetime
from django.db import models
from django.utils import timezone

# Domainの役割
class Schedule(models.Model):
    """スケジュール"""
    summary = models.CharField('タイトル')
    description = models.TextField('内容', blank=True)
    date = models.DateField('日付')
    created_at = models.DateTimeField('作成日', default=timezone.now)
    start_datetime = models.DateTimeField('開始日時', default=timezone.now)
    end_datetime = models.DateTimeField('終了日時', default=timezone.now)
    user_id = models.IntegerField('ユーザーID', default=1)
    project_id = models.IntegerField('プロジェクトID', default=1)
    reminder_task_id = models.CharField('タスクID',max_length=255, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    reminder_enabled = models.BooleanField('リマインダー有効', default=True)

    def __str__(self):
        return self.summary
