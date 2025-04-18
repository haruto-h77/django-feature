from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta,time

from .models import Schedule
from backend.app.tasks import send_reminder
from celery import current_app
import logging

# logger を設定
logger = logging.getLogger(__name__)

REMINDER_DEFAULT_MINUTES = 30

def save_task_id(instance, task_id):
    """
    タスクIDを保存する関数。
    シグナルを一時的に無効化して無限ループを防ぎます。
    """
    logger.info(f"--- save_task_id called for Schedule ID: {instance.id} with Task ID: {task_id} ---")
    post_save.disconnect(schedule_reminder_task, sender=Schedule)
    instance.reminder_task_id = task_id
    try:
        instance.save(update_fields=['reminder_task_id']) # 指定フィールドのみ更新
        logger.info(f"Successfully saved Task ID {task_id} for Schedule {instance.id}.")
    except Exception as e:
        logger.error(f"Error saving Task ID {task_id} for Schedule {instance.id}: {e}")
    finally:
        post_save.connect(schedule_reminder_task, sender=Schedule)
        logger.info(f"--- save_task_id finished for Schedule ID: {instance.id} ---")

def cancel_task_by_id(task_id, schedule_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセルします。
    実行中のタスクもterminate=Trueで強制停止します。
    """
    try:
        if task_id:
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Reminder task {task_id} canceled for schedule {schedule_id}.")
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id} for schedule {schedule_id}: {e}")

@receiver(post_save, sender=Schedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    """
    スケジュールが作成または更新されたときにリマインダーをスケジュールします。
    """

    scheduled_datetime = instance.start_datetime
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
            scheduled_datetime = make_aware(datetime.combine(instance.date, instance.start_time))
            reminder_time = scheduled_datetime - timedelta(minutes=REMINDER_DEFAULT_MINUTES)
            current_time = now()
            logger.info(f"Calculated reminder_time: {reminder_time}, scheduled_datetime: {scheduled_datetime}, current_time: {current_time}")

            # --- 新しいタスクのスケジュール ---
            if current_time < reminder_time:
                try:
                    task = send_reminder.apply_async(args=[instance.id], eta=reminder_time)
                    new_task_id = task.id
                    logger.info(f"Scheduled future reminder for Schedule {instance.id} at {reminder_time}. New Task ID: {new_task_id}")
                except Exception as e:
                    logger.error(f"Failed to schedule reminder task (eta) for Schedule {instance.id}: {e}")
            elif reminder_time <= current_time < scheduled_datetime:
                try:
                    task = send_reminder.apply_async(args=[instance.id])
                    new_task_id = task.id
                    logger.info(f"Scheduled immediate reminder for Schedule {instance.id}. New Task ID: {new_task_id}")
                except Exception as e:
                    logger.error(f"Failed to schedule reminder task (immediate) for Schedule {instance.id}: {e}")
            else:
                logger.info(f"Reminder not sent for Schedule {instance.id}. Scheduled time {scheduled_datetime} is in the past.")
                # new_task_id は None のまま

    # --- 新しいタスクIDを保存 ---
    # ★ DBに保存されている現在のタスクIDを再度確認 (instance.pk がある場合のみ) ★
    current_db_task_id_before_save = None
    if instance.pk:
        try:
            current_db_task_id_before_save = Schedule.objects.get(pk=instance.pk).reminder_task_id
            logger.info(f"Current task ID in DB before save for Schedule {instance.id}: {current_db_task_id_before_save}")
        except Schedule.DoesNotExist:
            logger.warning(f"Could not find Schedule {instance.id} in DB to check current task ID before save.")
    # else:
    #     logger.info(f"Instance pk is None, cannot fetch task ID from DB before save.")

    # ★ 新しいタスクIDとDBのタスクIDが異なる場合のみ保存処理を行う ★
    if new_task_id != current_db_task_id_before_save:
        logger.info(f"New task ID ({new_task_id}) is different from DB task ID ({current_db_task_id_before_save}). Calling save_task_id.")
        save_task_id(instance, new_task_id)
    else:
        # ★ 変更がない場合は保存しない ★
        logger.info(f"New task ID ({new_task_id}) is the same as DB task ID ({current_db_task_id_before_save}). No need to save.")

@receiver(post_delete, sender=Schedule)
def cancel_reminder_task(sender, instance, **kwargs):
    """
    スケジュール削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    # タスクIDを取得してキャンセル
    task_id = instance.reminder_task_id  # モデルにタスクIDを保存している場合
    cancel_task_by_id(task_id, instance.id)
