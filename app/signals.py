from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta

from .models import Schedule
from .tasks import send_reminder

@receiver(post_save, sender=Schedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    if created:
        dt_str = f"{instance.date} {instance.start_time}"
        scheduled_datetime = make_aware(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"))
        reminder_time = scheduled_datetime - timedelta(minutes=30)

        # 現在時刻を取得
        current_time = now()

        # 条件1: 現在時刻が開始時刻の30分前より前の場合
        if current_time < reminder_time:
            send_reminder.apply_async(
                args=[instance.id],
                eta=reminder_time
            )
        # 条件2: 現在時刻が開始時刻の30分前以降かつ開始時刻より前の場合
        elif reminder_time <= current_time < scheduled_datetime:
            send_reminder.apply_async(
                args=[instance.id]
            )
        # 条件3: 開始時刻が現在時刻より過去の場合
        else:
            # ログを記録する（任意）
            print(f"Reminder not sent. Scheduled time {scheduled_datetime} is in the past.")
