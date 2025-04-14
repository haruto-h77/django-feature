from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta

from .models import Schedule
from .tasks import send_reminder
from celery import current_app

def save_task_id(instance, task_id):
    """
    タスクIDを保存する関数。
    シグナルを一時的に無効化して無限ループを防ぎます。
    """
    from django.db.models.signals import post_save

    # シグナルを一時的に無効化
    post_save.disconnect(schedule_reminder_task, sender=Schedule)
    instance.reminder_task_id = task_id
    instance.save()
    # シグナルを再接続
    post_save.connect(schedule_reminder_task, sender=Schedule)

def cancel_task_by_id(task_id, schedule_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセルします。
    実行中のタスクもterminate=Trueで強制停止します。
    """
    try:
        if task_id:
            # Celeryの現在のアプリケーションからControlを使用
            current_app.control.revoke(task_id, terminate=True)
            print(f"Reminder task {task_id} canceled for schedule {schedule_id}.")
    except Exception as e:
        print(f"Failed to cancel task {task_id} for schedule {schedule_id}: {e}")

@receiver(post_save, sender=Schedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    """
    スケジュールが作成または更新されたときにリマインダーをスケジュールします。
    """
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
            save_task_id(instance, task.id)
        # 条件2: 現在時刻が開始時刻の30分前以降かつ開始時刻より前の場合
        elif reminder_time <= current_time <= scheduled_datetime:
            task = send_reminder.apply_async(
                args=[instance.id]
            )
            # タスクIDを保存
            save_task_id(instance, task.id)
        # 条件3: 開始時刻が現在時刻より過去の場合
        else:
            print(f"Reminder not sent. Scheduled time {scheduled_datetime} is in the past.")
    else:
        # 更新時の処理
        # 既存のリマインダーをキャンセル
        cancel_task_by_id(instance.reminder_task_id, instance.id)

        # 新しいリマインダーをスケジュール
        # 条件1: 現在時刻が開始時刻の30分前より前の場合
        if current_time < reminder_time:
            task = send_reminder.apply_async(
                args=[instance.id],
                eta=reminder_time
            )
            # タスクIDを保存
            save_task_id(instance, task.id)
        # 条件2: 現在時刻が開始時刻の30分前以降かつ開始時刻より前の場合
        elif reminder_time <= current_time <= scheduled_datetime:
            task = send_reminder.apply_async(
                args=[instance.id]
            )
            # タスクIDを保存
            save_task_id(instance, task.id)
        # 条件3: 開始時刻が現在時刻より過去の場合
        else:
            print(f"Reminder not sent. Scheduled time {scheduled_datetime} is in the past.")

@receiver(post_delete, sender=Schedule)
def cancel_reminder_task(sender, instance, **kwargs):
    """
    スケジュール削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    # タスクIDを取得してキャンセル
    task_id = instance.reminder_task_id  # モデルにタスクIDを保存している場合
    cancel_task_by_id(task_id, instance.id)
