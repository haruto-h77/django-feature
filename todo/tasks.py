# /home/hideaki/src/django-feature/todo/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta, datetime
from django.utils import timezone
# ScheduleではなくTodoモデルをインポート
from .models import Todo
import logging

logger = logging.getLogger(__name__)

# 既存のsend_reminderはapp用なので、コメントアウトするか削除、または別名にする
# @shared_task
# def send_reminder(schedule_id):
#     # ... (Schedule用のコード) ...

@shared_task
def send_todo_reminder(todo_id):
    """Todoのリマインダーメールを送信するタスク"""
    try:
        todo = Todo.objects.get(id=todo_id, is_deleted=False, finished_date__isnull=True) # 未完了かつ未削除のTodoを取得

        # 期限日時が存在する場合のみリマインダーを送信
        if todo.expire_datetime:
            # 期限日時を分かりやすい形式に変換
            expire_str = todo.expire_datetime.strftime("%Y年%m月%d日 %H時%M分")

            # メール本文を作成
            message = (
                f"Todo項目: {todo.item_name}\n"
                f"担当者: {todo.user.username}\n"
                f"期限日時: {expire_str}\n\n"
                f"このタスクの期限が近づいています。"
            )

            # メールを送信
            send_mail(
                f"Todoリマインダー: {todo.item_name}",  # 件名
                message,  # 本文
                'from@example.com',  # 送信元 (settings.pyで設定)
                [todo.user.email if todo.user.email else 'to@example.com'], # 送信先 (担当者のメールアドレス、なければデフォルト)
                fail_silently=False,
            )
            logger.info(f"Todo reminder sent for todo id {todo_id}")
        else:
            logger.info(f"Todo with id {todo_id} has no expire_datetime. Reminder not sent.")

    except Todo.DoesNotExist:
        logger.warning(f"Todo with id {todo_id} does not exist or is already completed/deleted. Reminder not sent.")
    except Exception as e:
        logger.error(f"Error sending todo reminder for id {todo_id}: {e}")
