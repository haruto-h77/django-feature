# /home/hideaki/src/django-feature/backend/todo/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import timedelta
import logging # logging をインポート

# TodoモデルとTodo用タスクをインポート
from .models import Todo
from backend.todo.tasks import send_todo_reminder # 作成したTodo用タスクをインポート
from celery import current_app

from backend.linker.state import SYNC_FLAG
from backend.linker.models import ScheduleTodoLink

# logger を設定
logger = logging.getLogger(__name__)

# リマインダーのデフォルト時間（分） 必要であれば settings.py などで定義
REMINDER_TODO_DEFAULT_MINUTES = 30

def save_todo_task_id(instance, task_id):
    """
    TodoのタスクIDを保存する関数 (シグナル制御付き、エラーハンドリング・ログあり)。
    """
    logger.info(f"--- save_todo_task_id called for Todo ID: {instance.id} with Task ID: {task_id} ---")
    # シグナルを一時的に無効化
    post_save.disconnect(schedule_todo_reminder_task_signal, sender=Todo)
    instance.reminder_todo_task_id = task_id
    try:
        # save() はDBエラー等を発生させる可能性があるため try は残す
        instance.save(update_fields=['reminder_todo_task_id'])
        logger.info(f"Successfully saved Task ID {task_id} for Todo {instance.id}.")
    except Exception as e:
        # ★★★ エラーログを追加 ★★★
        logger.error(f"Error saving Task ID {task_id} for Todo {instance.id}: {e}", exc_info=True)
    finally:
        # シグナルを再接続
        post_save.connect(schedule_todo_reminder_task_signal, sender=Todo)
        logger.info(f"--- save_todo_task_id finished for Todo ID: {instance.id} ---")

def cancel_task_by_id(task_id, todo_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセル (エラーハンドリング・ログあり)。
    """
    if task_id:
        logger.info(f"Attempting to cancel task {task_id} for todo {todo_id}.")
        try:
            # revoke() はCelery接続エラー等を発生させる可能性があるため try は残す
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Successfully requested cancellation for task {task_id} (todo {todo_id}).")
        except Exception as e:
            # ★★★ エラーログを追加 ★★★
            logger.error(f"Failed to cancel task {task_id} for todo {todo_id}: {e}", exc_info=True)
    else:
        logger.debug(f"No task ID provided for todo {todo_id}, cancellation skipped.")

def reschedule_todo_reminder(instance):
    """
    Todoインスタンスに基づいてリマインダータスクを再スケジュールする。
    (既存タスクキャンセル、新規スケジュール、タスクID保存)
    """
    logger.info(f"--- reschedule_todo_reminder called for Todo ID: {instance.id} ---")
    new_task_id = None
    current_db_task_id = None

    # --- 既存タスクIDの取得とキャンセルロジック ---
    if instance.pk: # DBに存在するインスタンスの場合のみ
        try:
            # DBから最新のタスクIDを取得 (instanceオブジェクトは古い可能性)
            db_instance = Todo.objects.only('reminder_todo_task_id').get(pk=instance.pk)
            current_db_task_id = db_instance.reminder_todo_task_id
            logger.info(f"Fetched current task ID from DB for Todo {instance.id}: {current_db_task_id}")
            # 既存タスクをキャンセルする
            if current_db_task_id:
                 logger.info(f"Canceling previous task {current_db_task_id} for Todo {instance.id} before rescheduling.")
                 cancel_task_by_id(current_db_task_id, instance.id)
        except Todo.DoesNotExist:
            logger.warning(f"Could not find Todo {instance.id} in DB during reschedule check. Skipping cancellation based on DB ID.")
        except Exception as e:
            logger.error(f"Error fetching task ID from DB for Todo {instance.id} during reschedule: {e}", exc_info=True)

    # --- リマインダー不要条件のチェック ---
    reminder_needed = True
    reason = ""
    if not instance.reminder_todo_enabled:
        reminder_needed = False
        reason = "disabled"
    elif not instance.expire_datetime:
        reminder_needed = False
        reason = "no expire_datetime"
    elif instance.finished_date:
        reminder_needed = False
        reason = "finished"
    elif instance.is_deleted:
        reminder_needed = False
        reason = "deleted"

    if not reminder_needed:
        logger.info(f"Reminder not needed for Todo {instance.id} (Reason: {reason}).")
        # タスクIDをNoneでクリアして保存 (DBの値と比較して変更があれば)
        # Note: キャンセルは上記で行われているはず
        if current_db_task_id is not None or instance.reminder_todo_task_id is not None:
             logger.info(f"Calling save_todo_task_id with None because reminder is not needed (Reason: {reason}).")
             save_todo_task_id(instance, None)
        else:
             logger.info(f"Task ID is already None in both DB and instance. No need to save None again.")
        logger.info(f"--- reschedule_todo_reminder finished early for Todo ID: {instance.id} ---")
        return # 処理終了

    # --- リマインダーが必要な場合の処理 ---
    logger.info(f"Reminder needed for Todo {instance.id}. Proceeding with scheduling logic.")
    # この時点では instance.expire_datetime は None でないことが保証されている
    reminder_time = instance.expire_datetime - timedelta(minutes=REMINDER_TODO_DEFAULT_MINUTES)
    current_time = now()
    logger.info(f"Calculated reminder_time: {reminder_time}, expire_datetime: {instance.expire_datetime}, current_time: {current_time}")

    # --- 新しいタスクのスケジュール ---
    try:
        # 条件1: 現在時刻がリマインダー時刻より前の場合 (未来のタスク)
        if current_time < reminder_time:
            task = send_todo_reminder.apply_async(args=[instance.id], eta=reminder_time)
            new_task_id = task.id
            logger.info(f"Scheduled future todo reminder for todo {instance.id} at {reminder_time}. New Task ID: {new_task_id}")
        # 条件2: 現在時刻がリマインダー時刻以降かつ期限時刻より前の場合 (即時実行に近いタスク)
        elif reminder_time <= current_time < instance.expire_datetime:
            task = send_todo_reminder.apply_async(args=[instance.id])
            new_task_id = task.id
            logger.info(f"Scheduled immediate todo reminder for todo {instance.id}. New Task ID: {new_task_id}")
        # 条件3: 期限時刻が現在時刻より過去の場合
        else:
            logger.info(f"Todo reminder not scheduled for todo {instance.id}. Expire datetime {instance.expire_datetime} is in the past.")
            new_task_id = None # 過去の場合も None

    except Exception as e:
        logger.error(f"Failed to schedule reminder for todo {instance.id}: {e}", exc_info=True)
        new_task_id = None # スケジュール失敗時は None にする

    # --- 新しいタスクIDを保存 ---
    final_db_task_id = None
    if instance.pk: # DBに存在するインスタンスの場合のみチェック
        try:
            # save_todo_task_id を呼ぶ *直前* のDBの状態を取得
            final_db_task_id = Todo.objects.only('reminder_todo_task_id').get(pk=instance.pk).reminder_todo_task_id
            logger.info(f"Final check: Current task ID in DB before save for Todo {instance.id}: {final_db_task_id}")
        except Todo.DoesNotExist:
             logger.warning(f"Could not find Todo {instance.id} before final save check.")
        except Exception as e:
            logger.error(f"Error fetching final task ID from DB for Todo {instance.id}: {e}", exc_info=True)

    # 新しいタスクIDとDBのタスクIDが異なる場合のみ保存処理を行う
    if new_task_id != final_db_task_id:
        logger.info(f"New task ID ({new_task_id}) is different from final DB task ID ({final_db_task_id}). Calling save_todo_task_id.")
        save_todo_task_id(instance, new_task_id)
    else:
        logger.info(f"New task ID ({new_task_id}) is the same as final DB task ID ({final_db_task_id}). No need to save.")

    logger.info(f"--- reschedule_todo_reminder finished for Todo ID: {instance.id} ---")

@receiver(post_save, sender=Todo)
def schedule_todo_reminder_task_signal(sender, instance, created, **kwargs):
    """
    Todoが保存されたときにリマインダー再スケジュール関数を呼び出すシグナルハンドラ。
    同期フラグをチェックして無限ループを防ぐ。
    """
    logger.info(f"--- schedule_todo_reminder_task_signal triggered for Todo ID: {instance.id} (created={created}) ---")

    # Scheduleからの同期によるsaveの場合は何もしない（linker側でrescheduleを呼ぶため）
    if SYNC_FLAG.get("from_schedule", False):
        logger.info(f"--- schedule_todo_reminder_task_signal skipped for Todo ID: {instance.id} because it was triggered by Schedule sync ---")
        return

    # 通常のTodo保存時（直接編集やAPI経由など）に再スケジュール処理を実行
    # ★★★ Linkerの作成元を確認し、'todo'の場合のみ実行 ★★★
    try:
        link = ScheduleTodoLink.objects.filter(todo=instance).first()
        # Linkerが存在しないか、作成元が 'todo' の場合にのみ再スケジュール
        if not link or link.created_from == 'todo':
            logger.info(f"Proceeding with reschedule_todo_reminder for Todo {instance.id} (created_from is 'todo' or not linked).")
            reschedule_todo_reminder(instance)
        else:
            logger.info(f"Skipping reschedule_todo_reminder for Todo {instance.id} because created_from is 'schedule'.")
    except Exception as e:
        logger.error(f"Error checking linker origin during schedule_todo_reminder_task_signal for Todo {instance.id}: {e}", exc_info=True)
        # エラー発生時は念のため再スケジュールしない

    logger.info(f"--- schedule_todo_reminder_task_signal finished for Todo ID: {instance.id} ---")


@receiver(post_delete, sender=Todo)
def cancel_todo_reminder_task_on_delete(sender, instance, **kwargs):
    """
    Todo削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    (関数名を変更して明確化)
    """
    task_id = instance.reminder_todo_task_id
    logger.info(f"--- cancel_todo_reminder_task_on_delete triggered for deleted Todo ID: {instance.id}, Task ID: {task_id} ---")
    cancel_task_by_id(task_id, instance.id)
    logger.info(f"--- cancel_todo_reminder_task_on_delete finished for deleted Todo ID: {instance.id} ---")
