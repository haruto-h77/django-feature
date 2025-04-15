from django.conf import settings
from django.db import models
from django.utils import timezone

class Todo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    registration_date = models.DateTimeField(blank=True,null=True)
    finished_date = models.DateTimeField(blank=True,null=True)
    expire_datetime = models.DateTimeField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    create_date_time = models.DateTimeField(default=timezone.now)
    update_date_time = models.DateTimeField(default=timezone.now)

    def publish(self):
        self.save()

    def __str__(self):
        return self.item_name

    @property
    def is_finished(self):
        if self.finished_date is None:
            return models.BooleanField(default=False)
        else:
            return models.BooleanField(default=True)

    @property
    def expire(self):
        # オプション: 完了済みの場合は期限切れとしない
        if self.finished_date:
            return False
        # expire_datetime が存在し (Noneでなく)、かつ現在時刻より前であれば True (期限切れ)
        if self.expire_datetime and self.expire_datetime < timezone.now():
            return True
        # expire_datetime が None か、未来の日付の場合は False (期限切れではない)
        return False
