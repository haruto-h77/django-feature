from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta, datetime
from django.utils import timezone
from .models import Schedule
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_reminder(schedule_id):
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        # メールを送信
        send_mail(
            f"Reminder: {schedule.summary}",
            schedule.description,
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
    except Schedule.DoesNotExist:
        pass
