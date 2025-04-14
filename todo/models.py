from django.conf import settings
from django.db import models
from django.utils import timezone

class Todo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    registration_date = models.DateTimeField(blank=True,null=True)
    expire_date = models.DateTimeField(blank=True,null=True)
    finished_date = models.DateTimeField(blank=True,null=True)
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
        return self.expire_date < timezone.now()
