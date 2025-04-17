import datetime
from django.db import models
from django.utils import timezone

# Domainの役割
class Schedule(models.Model):
    """スケジュール"""
    summary = models.CharField('タイトル')
    description = models.TextField('内容', blank=True)
    start_time = models.TimeField('開始時間', default=datetime.time(7, 0, 0))
    end_time = models.TimeField('終了時間', default=datetime.time(7, 0, 0))
    date = models.DateField('日付')
    created_at = models.DateTimeField('作成日', default=timezone.now)
    start_date = models.DateField('開始日', default=timezone.now)
    end_date = models.DateField('終了日', default=timezone.now)
    user_id = models.IntegerField('ユーザーID', default=1)
    project_id = models.IntegerField('プロジェクトID', default=1)
    reminder_task_id = models.CharField('タスクID',max_length=255, blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.summary
