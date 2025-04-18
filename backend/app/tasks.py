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
        
        if not schedule.reminder_enabled:
            logger.info(f"Reminder is disabled for Schedule {schedule_id}. Reminder not sent.")
            return # リマインダー無効なら終了
        
        if schedule.is_completed:
            logger.info(f"Schedule {schedule_id} is already completed. Reminder not sent.")
            return # 完了済みの場合はメールを送らずに終了
        
        # 時間をh時m分形式に変換
        start_time = schedule.start_time.strftime("%-H時%M分")  # %-H, %-Mでゼロ埋めを省略
        end_time = schedule.end_time.strftime("%-H時%M分")
        
        # メール本文をカスタマイズ
        message = (
            f"予定名: {schedule.summary}\n"
            f"説明: {schedule.description}\n"
            f"予定開始日時: {schedule.date} {start_time}\n"
            f"予定終了日時: {schedule.date} {end_time}\n\n"
        )
        
        # メールを送信
        send_mail(
            f"Reminder: {schedule.summary}",  # 件名
            message,  # 本文
            'from@example.com',  # 送信元
            ['to@example.com'],  # 送信先
            fail_silently=False,
        )
    except Schedule.DoesNotExist:
        logger.warning(f"Schedule with id {schedule_id} does not exist. Reminder not sent.")
