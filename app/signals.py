from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta

from .models import Schedule
from .tasks import send_reminder

@receiver(post_save, sender=Schedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    dt_str = f"{instance.date} {instance.start_time}"
    scheduled_datetime = make_aware(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"))
    reminder_time = scheduled_datetime - timedelta(minutes=30)

    # 現在時刻を取得
    current_time = now()

    if created:
        # 新規作成時の処理
        # 条件1: 現在時刻が開始時刻の30分前より前の場合
        if current_time < reminder_time:
            task = send_reminder.apply_async(
                args=[instance.id],
                eta=reminder_time
            )
            # タスクIDを保存
            instance.reminder_task_id = task.id
            instance.save()
        # 条件2: 現在時刻が開始時刻の30分前以降かつ開始時刻より前の場合
        elif reminder_time <= current_time <= scheduled_datetime:
            task = send_reminder.apply_async(
                args=[instance.id]
            )
            # タスクIDを保存
            instance.reminder_task_id = task.id
            instance.save()
        # 条件3: 開始時刻が現在時刻より過去の場合
        else:
            print(f"Reminder not sent. Scheduled time {scheduled_datetime} is in the past.")
    else:
        # 更新時の処理
        # 既存のリマインダーをキャンセル
        try:
            if instance.reminder_task_id:
                from celery.app.control import revoke
                revoke(instance.reminder_task_id, terminate=True)
                print(f"Previous reminder task {instance.reminder_task_id} canceled.")
        except Exception as e:
            print(f"Failed to cancel previous task: {e}")

        # 新しいリマインダーをスケジュール
        # 条件1: 現在時刻が開始時刻の30分前より前の場合
        if current_time < reminder_time:
            task = send_reminder.apply_async(
                args=[instance.id],
                eta=reminder_time
            )
            # タスクIDを保存
            instance.reminder_task_id = task.id
            instance.save()
        # 条件2: 現在時刻が開始時刻の30分前以降かつ開始時刻より前の場合
        elif reminder_time <= current_time <= scheduled_datetime:
            task = send_reminder.apply_async(
                args=[instance.id]
            )
            # タスクIDを保存
            instance.reminder_task_id = task.id
            instance.save()
        # 条件3: 開始時刻が現在時刻より過去の場合
        else:
            print(f"Reminder not sent. Scheduled time {scheduled_datetime} is in the past.")

@receiver(post_delete, sender=Schedule)
def cancel_reminder_task(sender, instance, **kwargs):
    # タスクをキャンセルする処理
    try:
        # CeleryのタスクIDを取得してキャンセル（タスクIDを保存している場合）
        task_id = instance.reminder_task_id  # モデルにタスクIDを保存している場合
        if task_id:
            from celery.app.control import revoke
            revoke(task_id, terminate=True)
            print(f"Reminder task {task_id} canceled for schedule {instance.id}.")
    except AttributeError:
        print(f"No task ID found for schedule {instance.id}.")
