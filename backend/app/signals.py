# /home/hideaki/src/django-feature/backend/app/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import datetime, timedelta,time

from .models import Schedule
from backend.app.tasks import send_reminder
from celery import current_app
import logging
# ★★★ state.py から SYNC_FLAG をインポート ★★★
from backend.linker.state import SYNC_FLAG
# ★★★ Linkerモデルをインポート ★★★
from backend.linker.models import ScheduleTodoLink

# logger を設定
logger = logging.getLogger(__name__)

REMINDER_DEFAULT_MINUTES = 30

# --- ヘルパー関数 (変更なし) ---
def save_task_id(instance, task_id):
    """
    タスクIDを保存する関数。
    シグナルを一時的に無効化して無限ループを防ぎます。
    """
    logger.info(f"--- save_task_id called for Schedule ID: {instance.id} with Task ID: {task_id} ---")
    # ↓↓↓ シグナルハンドラ名を新しい名前に変更 ↓↓↓
    post_save.disconnect(schedule_reminder_task_signal, sender=Schedule)
    instance.reminder_task_id = task_id
    try:
        instance.save(update_fields=['reminder_task_id']) # 指定フィールドのみ更新
        logger.info(f"Successfully saved Task ID {task_id} for Schedule {instance.id}.")
    except Exception as e:
        logger.error(f"Error saving Task ID {task_id} for Schedule {instance.id}: {e}", exc_info=True)
    finally:
        # ↓↓↓ シグナルハンドラ名を新しい名前に変更 ↓↓↓
        post_save.connect(schedule_reminder_task_signal, sender=Schedule)
        logger.info(f"--- save_task_id finished for Schedule ID: {instance.id} ---")

def cancel_task_by_id(task_id, schedule_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセルします。
    実行中のタスクもterminate=Trueで強制停止します。
    """
    if task_id:
        logger.info(f"Attempting to cancel task {task_id} for schedule {schedule_id}.")
        try:
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Successfully requested cancellation for task {task_id} (schedule {schedule_id}).")
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id} for schedule {schedule_id}: {e}", exc_info=True)
    else:
        logger.debug(f"No task ID provided for schedule {schedule_id}, cancellation skipped.")

# --- ★★★ リマインダー再スケジュール処理を関数化 ★★★ ---
def reschedule_schedule_reminder(instance):
    """
    Scheduleインスタンスに基づいてリマインダータスクを再スケジュールする。
    (既存タスクキャンセル、新規スケジュール、タスクID保存)
    """
    logger.info(f"--- reschedule_schedule_reminder called for Schedule ID: {instance.id} ---")
    new_task_id = None
    current_db_task_id = None

    # --- 既存タスクIDの取得とキャンセルロジック ---
    if instance.pk: # DBに存在するインスタンスの場合のみ
        try:
            # DBから最新のタスクIDを取得 (instanceオブジェクトは古い可能性)
            db_instance = Schedule.objects.only('reminder_task_id').get(pk=instance.pk)
            current_db_task_id = db_instance.reminder_task_id
            logger.info(f"Fetched current task ID from DB for Schedule {instance.id}: {current_db_task_id}")
            # 既存タスクをキャンセルする
            if current_db_task_id:
                 logger.info(f"Canceling previous task {current_db_task_id} for Schedule {instance.id} before rescheduling.")
                 cancel_task_by_id(current_db_task_id, instance.id)
        except Schedule.DoesNotExist:
            logger.warning(f"Could not find Schedule {instance.id} in DB during reschedule check. Skipping cancellation based on DB ID.")
        except Exception as e:
            logger.error(f"Error fetching task ID from DB for Schedule {instance.id}: {e}", exc_info=True)

    # --- リマインダー不要条件のチェック ---
    reminder_needed = True
    reason = ""
    if not instance.reminder_enabled:
        reminder_needed = False
        reason = "disabled"
    elif instance.is_completed:
        reminder_needed = False
        reason = "completed"
    elif not instance.start_datetime: # start_datetime がないとリマインダー時刻を計算できない
        reminder_needed = False
        reason = "no start_datetime"

    if not reminder_needed:
        logger.info(f"Reminder not needed for Schedule {instance.id} (Reason: {reason}).")
        # タスクIDをNoneでクリアして保存 (DBの値と比較して変更があれば)
        if current_db_task_id is not None or instance.reminder_task_id is not None:
             logger.info(f"Calling save_task_id with None because reminder is not needed (Reason: {reason}).")
             save_task_id(instance, None)
        else:
             logger.info(f"Task ID is already None in both DB and instance. No need to save None again.")
        logger.info(f"--- reschedule_schedule_reminder finished early for Schedule ID: {instance.id} ---")
        return # 処理終了

    # --- リマインダーが必要な場合の処理 ---
    logger.info(f"Reminder needed for Schedule {instance.id}. Proceeding with scheduling logic.")
    # この時点では instance.start_datetime は None でないことが保証されている
    reminder_time = instance.start_datetime - timedelta(minutes=REMINDER_DEFAULT_MINUTES)
    current_time = now()
    logger.info(f"Calculated reminder_time: {reminder_time}, start_datetime: {instance.start_datetime}, current_time: {current_time}")

    # --- 新しいタスクのスケジュール ---
    try:
        # 条件1: 現在時刻がリマインダー時刻より前の場合 (未来のタスク)
        if current_time < reminder_time:
            task = send_reminder.apply_async(args=[instance.id], eta=reminder_time)
            new_task_id = task.id
            logger.info(f"Scheduled future reminder for Schedule {instance.id} at {reminder_time}. New Task ID: {new_task_id}")
        # 条件2: 現在時刻がリマインダー時刻以降かつスケジュール開始時刻より前の場合 (即時実行に近いタスク)
        elif reminder_time <= current_time < instance.start_datetime:
            task = send_reminder.apply_async(args=[instance.id])
            new_task_id = task.id
            logger.info(f"Scheduled immediate reminder for Schedule {instance.id}. New Task ID: {new_task_id}")
        # 条件3: スケジュール開始時刻が現在時刻より過去の場合
        else:
            logger.info(f"Reminder not scheduled for Schedule {instance.id}. Start datetime {instance.start_datetime} is in the past.")
            new_task_id = None # 過去の場合も None

    except Exception as e:
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
             logger.warning(f"Could not find Schedule {instance.id} before final save check.")
        except Exception as e:
            logger.error(f"Error fetching final task ID from DB for Schedule {instance.id}: {e}", exc_info=True)

    # 新しいタスクIDとDBのタスクIDが異なる場合のみ保存処理を行う
    if new_task_id != final_db_task_id:
        logger.info(f"New task ID ({new_task_id}) is different from final DB task ID ({final_db_task_id}). Calling save_task_id.")
        save_task_id(instance, new_task_id)
    else:
        logger.info(f"New task ID ({new_task_id}) is the same as final DB task ID ({final_db_task_id}). No need to save.")

    logger.info(f"--- reschedule_schedule_reminder finished for Schedule ID: {instance.id} ---")


# --- ★★★ シグナルハンドラ (名前変更) ★★★ ---
@receiver(post_save, sender=Schedule)
def schedule_reminder_task_signal(sender, instance, created, **kwargs):
    """
    Scheduleが保存されたときにリマインダー再スケジュール関数を呼び出すシグナルハンドラ。
    同期フラグと作成元をチェックして無限ループや二重処理を防ぐ。
    """
    logger.info(f"--- schedule_reminder_task_signal triggered for Schedule ID: {instance.id} (created={created}) ---")

    # Todoからの同期によるsaveの場合は何もしない（linker側でrescheduleを呼ぶため）
    if SYNC_FLAG.get("from_todo", False):
        logger.info(f"--- schedule_reminder_task_signal skipped for Schedule ID: {instance.id} because it was triggered by Todo sync ---")
        return

    # 通常のSchedule保存時（直接編集やAPI経由など）に再スケジュール処理を実行
    # ★★★ Linkerの作成元を確認し、'schedule'の場合のみ実行 ★★★
    try:
        link = ScheduleTodoLink.objects.filter(schedule=instance).first()
        # Linkerが存在しないか、作成元が 'schedule' の場合にのみ再スケジュール
        if not link or link.created_from == 'schedule':
            logger.info(f"Proceeding with reschedule_schedule_reminder for Schedule {instance.id} (created_from is 'schedule' or not linked).")
            reschedule_schedule_reminder(instance)
        else:
            logger.info(f"Skipping reschedule_schedule_reminder for Schedule {instance.id} because created_from is 'todo'.")
    except Exception as e:
        logger.error(f"Error checking linker origin during schedule_reminder_task_signal for Schedule {instance.id}: {e}", exc_info=True)
        # エラー発生時は念のため再スケジュールしない

    logger.info(f"--- schedule_reminder_task_signal finished for Schedule ID: {instance.id} ---")


# --- 削除時シグナルハンドラ (変更なし) ---
@receiver(post_delete, sender=Schedule)
def cancel_reminder_task(sender, instance, **kwargs):
    """
    スケジュール削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    task_id = instance.reminder_task_id
    logger.info(f"--- cancel_reminder_task triggered for deleted Schedule ID: {instance.id}, Task ID: {task_id} ---")
    cancel_task_by_id(task_id, instance.id)
    logger.info(f"--- cancel_reminder_task finished for deleted Schedule ID: {instance.id} ---")
