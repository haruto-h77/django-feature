# /home/hideaki/src/django-feature/todo/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import timedelta

# TodoモデルとTodo用タスクをインポート
from .models import Todo
from .tasks import send_todo_reminder # 作成したTodo用タスクをインポート
from celery import current_app
import logging

logger = logging.getLogger(__name__)

def save_todo_task_id(instance, task_id):
    """
    TodoのタスクIDを保存する関数。
    シグナルを一時的に無効化して無限ループを防ぎます。
    """
    # シグナルを一時的に無効化 (senderをTodoに変更)
    post_save.disconnect(schedule_todo_reminder_task, sender=Todo)
    instance.reminder_todo_task_id = task_id
    instance.save(update_fields=['reminder_todo_task_id']) # 指定フィールドのみ更新
    # シグナルを再接続 (senderをTodoに変更)
    post_save.connect(schedule_todo_reminder_task, sender=Todo)
    logger.info(f"Saved reminder task id {task_id} for todo {instance.id}")

def cancel_task_by_id(task_id, todo_id):
    """
    指定されたタスクIDのCeleryタスクをキャンセルします。
    実行中のタスクもterminate=Trueで強制停止します。
    """
    try:
        if task_id:
            # Celeryの現在のアプリケーションからControlを使用
            current_app.control.revoke(task_id, terminate=True)
            logger.info(f"Reminder task {task_id} canceled for todo {todo_id}.")
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id} for todo {todo_id}: {e}")

@receiver(post_save, sender=Todo)
def schedule_todo_reminder_task(sender, instance, created, **kwargs):
    """
    Todoが作成または更新されたときにリマインダーをスケジュールします。
    期限があり、未完了、未削除の場合にスケジュールされます。
    """
    # 期限がない、完了済み、削除済み、またはリマインダー設定がない場合は何もしない
    if not instance.expire_datetime or instance.finished_date or instance.is_deleted:
        # もし既存のタスクがあればキャンセルする（例：完了した場合など）
        if instance.reminder_todo_task_id:
            cancel_task_by_id(instance.reminder_todo_task_id, instance.id)
            save_todo_task_id(instance, None) # タスクIDをクリア
        return

    # リマインダー送信時刻を計算 (例: 期限の30分前)
    reminder_time = instance.expire_datetime - timedelta(minutes=30)
    current_time = now()

    # --- 更新時の処理 ---
    if not created:
        # 既存のリマインダーがあればキャンセル
        cancel_task_by_id(instance.reminder_todo_task_id, instance.id)
        # タスクIDを一旦クリア（新しいタスクがスケジュールされなかった場合に備える）
        instance.reminder_todo_task_id = None

    # --- 新規作成時 または 更新時でリマインダーが必要な場合 ---
    new_task_id = None
    # 条件1: 現在時刻がリマインダー時刻より前の場合 (未来のタスク)
    if current_time < reminder_time:
        try:
            task = send_todo_reminder.apply_async(
                args=[instance.id],
                eta=reminder_time
            )
            new_task_id = task.id
            logger.info(f"Scheduled todo reminder for todo {instance.id} at {reminder_time}")
        except Exception as e:
            logger.error(f"Failed to schedule future reminder for todo {instance.id}: {e}")
    # 条件2: 現在時刻がリマインダー時刻以降かつ期限時刻より前の場合 (即時実行に近いタスク)
    elif reminder_time <= current_time < instance.expire_datetime:
        try:
            # すぐに実行されるようにetaなしでスケジュール
            task = send_todo_reminder.apply_async(
                args=[instance.id],
            )
            new_task_id = task.id
            logger.info(f"Scheduled immediate todo reminder for todo {instance.id}")
        except Exception as e:
            logger.error(f"Failed to schedule immediate reminder for todo {instance.id}: {e}")
    # 条件3: 期限時刻が現在時刻より過去の場合
    else:
        logger.info(f"Todo reminder not scheduled for todo {instance.id}. Expire datetime {instance.expire_datetime} is in the past.")

    # 新しいタスクIDが生成された場合のみ保存
    if new_task_id:
        save_todo_task_id(instance, new_task_id)
    elif not created and instance.reminder_todo_task_id is not None:
        # 更新時に新しいタスクがスケジュールされず、古いタスクIDが残っている場合はクリア
        save_todo_task_id(instance, None)


@receiver(post_delete, sender=Todo)
def cancel_todo_reminder_task(sender, instance, **kwargs):
    """
    Todo削除時に関連するリマインダー（Celeryタスク）をキャンセルします。
    """
    # タスクIDを取得してキャンセル (Todoモデルのフィールド名に変更)
    task_id = instance.reminder_todo_task_id
    cancel_task_by_id(task_id, instance.id)
