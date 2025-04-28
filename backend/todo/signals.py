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

from backend.linker.signals import SYNC_FLAG

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
    post_save.disconnect(schedule_todo_reminder_task, sender=Todo)
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
        post_save.connect(schedule_todo_reminder_task, sender=Todo)
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


@receiver(post_save, sender=Todo)
def schedule_todo_reminder_task(sender, instance, created, **kwargs):
    """
    Todoが作成または更新されたときにリマインダーをスケジュール/キャンセルします。
    reminder_todo_enabled=True で、期限があり、未完了、未削除の場合にスケジュールされます。
    """
    # ★★★ 処理開始ログ ★★★
    logger.info(f"--- schedule_todo_reminder_task triggered for Todo ID: {instance.id} (created={created}) ---")

    new_task_id = None
    current_db_task_id = None
    if SYNC_FLAG.get("from_schedule", False):
        logger.info(f"--- schedule_todo_reminder_task skipped for Todo ID: {instance.id} because it was triggered by Schedule sync ---")
        return
    # --- 既存タスクIDの取得とキャンセルロジック (更新時など) ---
    if not created and instance.pk: # 更新時 かつ DBに存在するインスタンスの場合
        try:
            # DBから最新のタスクIDを取得 (instanceオブジェクトは古い可能性)
            db_instance = Todo.objects.only('reminder_todo_task_id').get(pk=instance.pk)
            current_db_task_id = db_instance.reminder_todo_task_id
            logger.info(f"Fetched current task ID from DB for Todo {instance.id}: {current_db_task_id}")
            # 更新時は既存タスクをキャンセルする（時刻変更、無効化などに備える）
            if current_db_task_id:
                 logger.info(f"Canceling previous task {current_db_task_id} for Todo {instance.id} due to update.")
                 cancel_task_by_id(current_db_task_id, instance.id)
        except Todo.DoesNotExist:
            # ★★★ 警告ログを追加 ★★★
            logger.warning(f"Could not find Todo {instance.id} in DB during update check. Skipping cancellation based on DB ID.")
        except Exception as e:
            # ★★★ その他のDBエラーログ ★★★
            logger.error(f"Error fetching task ID from DB for Todo {instance.id}: {e}", exc_info=True)


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
        # ★★★ リマインダー不要時のログ ★★★
        logger.info(f"Reminder not needed for Todo {instance.id} (Reason: {reason}). Checking if task needs cancellation.")
        # リマインダー不要なら、既存タスクをキャンセル (更新時以外も考慮)
        task_id_to_cancel = current_db_task_id or instance.reminder_todo_task_id
        if task_id_to_cancel:
            cancel_task_by_id(task_id_to_cancel, instance.id)

        # タスクIDをNoneでクリアして保存 (DBの値と比較して変更があれば)
        if current_db_task_id is not None or instance.reminder_todo_task_id is not None:
             logger.info(f"Calling save_todo_task_id with None because reminder is not needed (Reason: {reason}).")
             save_todo_task_id(instance, None)
        else:
             logger.info(f"Task ID is already None in both DB and instance. No need to save None again.")

        # ★★★ 処理終了ログ ★★★
        logger.info(f"--- schedule_todo_reminder_task finished early for Todo ID: {instance.id} ---")
        return # 処理終了

    # --- リマインダーが必要な場合の処理 ---
    # ★★★ リマインダー必要時のログ ★★★
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
        # ★★★ スケジュール失敗時のエラーログ ★★★
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
             # ★★★ 警告ログを追加 ★★★
             logger.warning(f"Could not find Todo {instance.id} before final save check.")
        except Exception as e:
            # ★★★ その他のDBエラーログ ★★★
            logger.error(f"Error fetching final task ID from DB for Todo {instance.id}: {e}", exc_info=True)


    # 新しいタスクIDとDBのタスクIDが異なる場合のみ保存処理を行う
    if new_task_id != final_db_task_id:
        logger.info(f"New task ID ({new_task_id}) is different from final DB task ID ({final_db_task_id}). Calling save_todo_task_id.")
        save_todo_task_id(instance, new_task_id)
    else:
        # ★★★ 保存不要時のログ ★★★
        logger.info(f"New task ID ({new_task_id}) is the same as final DB task ID ({final_db_task_id}). No need to save.")

    # ★★★ 処理終了ログ ★★★
    logger.info(f"--- schedule_todo_reminder_task finished for Todo ID: {instance.id} ---")


@receiver(post_delete, sender=Todo)
def cancel_todo_reminder_task(sender, instance, **kwargs):
    """
    Todo削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    task_id = instance.reminder_todo_task_id
    # ★★★ 処理開始ログ ★★★
    logger.info(f"--- cancel_todo_reminder_task triggered for deleted Todo ID: {instance.id}, Task ID: {task_id} ---")
    cancel_task_by_id(task_id, instance.id)
    # ★★★ 処理終了ログ ★★★
    logger.info(f"--- cancel_todo_reminder_task finished for deleted Todo ID: {instance.id} ---")
