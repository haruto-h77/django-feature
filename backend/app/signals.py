# /home/hideaki/src/django-feature/backend/app/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import datetime, timedelta,time

from .models import Schedule
from backend.app.tasks import send_reminder
from celery import current_app
import logging
from backend.linker.signals import SYNC_FLAG

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
        # ★★★ エラーログを改善 ★★★
        logger.error(f"Error saving Task ID {task_id} for Schedule {instance.id}: {e}", exc_info=True)
    finally:
        post_save.connect(schedule_reminder_task, sender=Schedule)
        logger.info(f"--- save_task_id finished for Schedule ID: {instance.id} ---")

def cancel_task_by_id(task_id, schedule_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセルします。
    実行中のタスクもterminate=Trueで強制停止します。
    """
    # ★★★ task_id が存在する場合のみキャンセル処理を実行 ★★★
    if task_id:
        logger.info(f"Attempting to cancel task {task_id} for schedule {schedule_id}.")
        try:
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Successfully requested cancellation for task {task_id} (schedule {schedule_id}).")
        except Exception as e:
            # ★★★ エラーログを改善 ★★★
            logger.error(f"Failed to cancel task {task_id} for schedule {schedule_id}: {e}", exc_info=True)
    else:
        logger.debug(f"No task ID provided for schedule {schedule_id}, cancellation skipped.")


@receiver(post_save, sender=Schedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    """
    スケジュールが作成または更新されたときにリマインダーをスケジュール/キャンセルします。
    reminder_enabled=True で、未完了の場合にスケジュールされます。
    """
    logger.info(f"--- schedule_reminder_task triggered for Schedule ID: {instance.id} (created={created}) ---")
    
    if SYNC_FLAG.get("from_todo", False):
        logger.info(f"--- schedule_reminder_task skipped for Schedule ID: {instance.id} because it was triggered by Todo sync ---")
        return
    new_task_id = None
    current_db_task_id = None

    # --- 既存タスクIDの取得とキャンセルロジック (更新時など) ---
    if not created and instance.pk: # 更新時 かつ DBに存在するインスタンスの場合
        try:
            # DBから最新のタスクIDを取得 (instanceオブジェクトは古い可能性)
            db_instance = Schedule.objects.only('reminder_task_id').get(pk=instance.pk)
            current_db_task_id = db_instance.reminder_task_id
            logger.info(f"Fetched current task ID from DB for Schedule {instance.id}: {current_db_task_id}")
            # 更新時は既存タスクをキャンセルする（時刻変更、無効化などに備える）
            if current_db_task_id:
                 logger.info(f"Canceling previous task {current_db_task_id} for Schedule {instance.id} due to update.")
                 cancel_task_by_id(current_db_task_id, instance.id)
        except Schedule.DoesNotExist:
            # ★★★ 警告ログを追加 ★★★
            logger.warning(f"Could not find Schedule {instance.id} in DB during update check. Skipping cancellation based on DB ID.")
        except Exception as e:
            # ★★★ その他のDBエラーログ ★★★
            logger.error(f"Error fetching task ID from DB for Schedule {instance.id}: {e}", exc_info=True)


    # --- リマインダー不要条件のチェック ---
    # reminder_enabled が False、または is_completed が True の場合はリマインダー不要
    reminder_needed = True
    reason = ""
    if not instance.reminder_enabled:
        reminder_needed = False
        reason = "disabled"
    elif instance.is_completed:
        reminder_needed = False
        reason = "completed"
    # ★★★ start_datetime がない場合もリマインダー不要 ★★★
    elif not instance.start_datetime:
        reminder_needed = False
        reason = "no start_datetime"

    if not reminder_needed:
        # ★★★ リマインダー不要時のログ ★★★
        logger.info(f"Reminder not needed for Schedule {instance.id} (Reason: {reason}). Checking if task needs cancellation.")

        # リマインダー不要なら、既存タスクをキャンセル (更新時以外も考慮)
        # current_db_task_id は更新時に取得したDBの値、instance.reminder_task_id は現在のインスタンスの値
        task_id_to_cancel = current_db_task_id or instance.reminder_task_id
        if task_id_to_cancel:
            cancel_task_by_id(task_id_to_cancel, instance.id)

        # タスクIDをNoneでクリアして保存 (DBの値と比較して変更があれば)
        # DBの最新値(current_db_task_id)か、インスタンスの値(instance.reminder_task_id)のどちらかがNoneでない場合、
        # Noneで上書きする必要がある。
        if current_db_task_id is not None or instance.reminder_task_id is not None:
             logger.info(f"Calling save_task_id with None because reminder is not needed (Reason: {reason}).")
             save_task_id(instance, None) # new_task_id は既に None
        else:
             logger.info(f"Task ID is already None in both DB and instance. No need to save None again.")

        # ★★★ 処理終了ログ ★★★
        logger.info(f"--- schedule_reminder_task finished early for Schedule ID: {instance.id} ---")
        return # 処理終了


    # --- リマインダーが必要な場合の処理 ---
    # ★★★ リマインダー必要時のログ ★★★
    logger.info(f"Reminder needed for Schedule {instance.id} (reminder_enabled=True, is_completed=False, start_datetime exists). Proceeding with scheduling logic.")

    # --- リマインダー時刻の計算 ---
    # この時点では instance.start_datetime は None でないことが保証されている
    scheduled_datetime = instance.start_datetime
    reminder_time = scheduled_datetime - timedelta(minutes=REMINDER_DEFAULT_MINUTES)
    current_time = now()
    logger.info(f"Calculated reminder_time: {reminder_time}, scheduled_datetime: {scheduled_datetime}, current_time: {current_time}")


    # --- 新しいタスクのスケジュール ---
    try:
        # 条件1: 現在時刻がリマインダー時刻より前の場合 (未来のタスク)
        if current_time < reminder_time:
            task = send_reminder.apply_async(args=[instance.id], eta=reminder_time)
            new_task_id = task.id
            logger.info(f"Scheduled future reminder for Schedule {instance.id} at {reminder_time}. New Task ID: {new_task_id}")
        # 条件2: 現在時刻がリマインダー時刻以降かつスケジュール時刻より前の場合 (即時実行に近いタスク)
        elif reminder_time <= current_time < scheduled_datetime:
            task = send_reminder.apply_async(args=[instance.id])
            new_task_id = task.id
            logger.info(f"Scheduled immediate reminder for Schedule {instance.id}. New Task ID: {new_task_id}")
        # 条件3: スケジュール時刻が現在時刻より過去の場合
        else:
            logger.info(f"Reminder not scheduled for Schedule {instance.id}. Scheduled time {scheduled_datetime} is in the past.")
            new_task_id = None # 過去の場合も None

    except Exception as e:
        # ★★★ スケジュール失敗時のエラーログ ★★★
        logger.error(f"Failed to schedule reminder task for Schedule {instance.id}: {e}", exc_info=True)
        new_task_id = None # スケジュール失敗時は None にする


    # --- 新しいタスクIDを保存 ---
    final_db_task_id = None
    if instance.pk: # DBに存在するインスタンスの場合のみチェック
        try:
            # save_task_id を呼ぶ *直前* のDBの状態を取得
            final_db_task_id = Schedule.objects.only('reminder_task_id').get(pk=instance.pk).reminder_task_id
            logger.info(f"Final check: Current task ID in DB before save for Schedule {instance.id}: {final_db_task_id}")
        except Schedule.DoesNotExist:
             # ★★★ 警告ログを追加 ★★★
             logger.warning(f"Could not find Schedule {instance.id} before final save check.")
        except Exception as e:
            # ★★★ その他のDBエラーログ ★★★
            logger.error(f"Error fetching final task ID from DB for Schedule {instance.id}: {e}", exc_info=True)


    # 新しいタスクIDとDBのタスクIDが異なる場合のみ保存処理を行う
    if new_task_id != final_db_task_id:
        logger.info(f"New task ID ({new_task_id}) is different from final DB task ID ({final_db_task_id}). Calling save_task_id.")
        save_task_id(instance, new_task_id)
    else:
        # ★★★ 保存不要時のログ ★★★
        logger.info(f"New task ID ({new_task_id}) is the same as final DB task ID ({final_db_task_id}). No need to save.")

    # ★★★ 処理終了ログ ★★★
    logger.info(f"--- schedule_reminder_task finished for Schedule ID: {instance.id} ---")


@receiver(post_delete, sender=Schedule)
def cancel_reminder_task(sender, instance, **kwargs):
    """
    スケジュール削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    task_id = instance.reminder_task_id
    # ★★★ 処理開始ログ ★★★
    logger.info(f"--- cancel_reminder_task triggered for deleted Schedule ID: {instance.id}, Task ID: {task_id} ---")
    cancel_task_by_id(task_id, instance.id)
    # ★★★ 処理終了ログ ★★★
    logger.info(f"--- cancel_reminder_task finished for deleted Schedule ID: {instance.id} ---")
