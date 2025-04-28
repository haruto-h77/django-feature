# /home/hideaki/src/django-feature/backend/linker/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from backend.app.models import Schedule
from backend.todo.models import Todo
from .models import ScheduleTodoLink
from datetime import datetime
from django.utils import timezone
from pytz import timezone as pytz_timezone
import logging # ロギングを追加

# ★★★ state.py から SYNC_FLAG をインポート ★★★
from .state import SYNC_FLAG
# ★★★ reschedule_... 関数のインポート ★★★
from backend.todo.signals import reschedule_todo_reminder
# from backend.app.signals import reschedule_schedule_reminder # app側の関数もインポート (仮)

logger = logging.getLogger(__name__) # logger を設定

# 無限ループ対応フラグは state.py に移動したので削除
# SYNC_FLAG = {"from_schedule": False, "from_todo": False} # ← 削除

# Schedule側でpost_saveされた場合
@receiver(post_save, sender=Schedule)
def sync_from_schedule(sender, instance, created, **kwargs):
    logger.info(f"--- sync_from_schedule triggered for Schedule ID: {instance.id} (created={created}) ---")
    if SYNC_FLAG["from_todo"]:
        logger.info(f"--- sync_from_schedule skipped for Schedule ID: {instance.id} due to SYNC_FLAG['from_todo'] ---")
        return

    SYNC_FLAG["from_schedule"] = True
    saved_todo = None # 保存されたTodoインスタンスを保持する変数
    link = None # Linkインスタンスを保持する変数
    try:
        link = ScheduleTodoLink.objects.filter(schedule=instance).first()
        if link:
            todo = link.todo
            logger.info(f"Found existing link for Schedule {instance.id} to Todo {todo.id}.")
            # 変更があったフィールドのみ更新する方が効率的だが、簡略化のため全同期
            todo.item_name = instance.summary
            todo.description = instance.description
            todo.expire_datetime = instance.end_datetime
            todo.reminder_todo_enabled = instance.reminder_enabled
            todo.save()
            saved_todo = todo # 保存したインスタンスを保持
            logger.info(f"Updated Todo {todo.id} from Schedule {instance.id}.")
        else:
            logger.info(f"No existing link found for Schedule {instance.id}. Creating new Todo and Link.")
            # 新規作成
            todo = Todo.objects.create(
                user_id=instance.user_id, # user_id を Schedule から取得
                item_name=instance.summary,
                description=instance.description,
                registration_date=instance.created_at, # Schedule の作成日時を使用
                expire_datetime=instance.end_datetime,
                reminder_todo_enabled=instance.reminder_enabled,
            )
            # ★★★ Linker作成時に created_from を指定 ★★★
            link = ScheduleTodoLink.objects.create(schedule=instance, todo=todo, created_from="schedule")
            saved_todo = todo # 保存したインスタンスを保持
            logger.info(f"Created new Todo {todo.id} and Link {link.id} from Schedule {instance.id} (created_from='schedule').")

        # ★★★ Todo保存後に、作成元に基づいてリマインダー再スケジュール処理を呼び出す ★★★
        if saved_todo and link: # saved_todo と link の両方が存在することを確認
            if link.created_from == 'todo':
                 logger.info(f"Calling reschedule_todo_reminder for Todo {saved_todo.id} from sync_from_schedule (created_from='todo').")
                 reschedule_todo_reminder(saved_todo) # Todo由来ならTodoのリマインダーを再スケジュール
            else: # created_from == 'schedule' の場合は何もしない (Schedule側のリマインダーが担当)
               logger.info(f"Skipping reschedule_todo_reminder for Todo {saved_todo.id} from sync_from_schedule (created_from='schedule').")
        elif saved_todo:
            logger.warning(f"Link object was not available after saving Todo {saved_todo.id} in sync_from_schedule. Skipping reschedule check.")
        else:
            logger.warning("Saved Todo object was not available in sync_from_schedule. Skipping reschedule check.")

    except Exception as e: # エラーハンドリングを追加
        logger.error(f"Error in sync_from_schedule for Schedule {instance.id}: {e}", exc_info=True)
    finally:
        SYNC_FLAG["from_schedule"] = False
        logger.info(f"--- sync_from_schedule finished for Schedule ID: {instance.id} ---")

# Schedule側でpre_deleteされた場合 (ログ追加)
@receiver(pre_delete, sender=Schedule)
def sync_delete_from_schedule(sender, instance, **kwargs):
    logger.info(f"--- sync_delete_from_schedule triggered for Schedule ID: {instance.id} ---")
    links = ScheduleTodoLink.objects.filter(schedule=instance)
    if not links.exists():
        logger.info(f"No links found for Schedule {instance.id}. Skipping delete sync.")
        return
    # linkerが存在していた場合はtodoを論理削除 linker自体はSchdule側の物理削除で削除される
    for link in links:
        linked_todo = link.todo
        logger.info(f"Logically deleting Todo {linked_todo.id} linked to Schedule {instance.id}.")
        linked_todo.is_deleted = True  # 論理削除
        linked_todo.save()
    logger.info(f"--- sync_delete_from_schedule finished for Schedule ID: {instance.id} ---")


# Todo側でpost_saveされた場合
@receiver(post_save, sender=Todo)
def sync_from_todo(sender, instance, created, **kwargs):
    logger.info(f"--- sync_from_todo triggered for Todo ID: {instance.id} (created={created}) ---")
    if SYNC_FLAG["from_schedule"]:
        logger.info(f"--- sync_from_todo skipped for Todo ID: {instance.id} due to SYNC_FLAG['from_schedule'] ---")
        return

    # 論理削除時の処理 (ログ追加)
    if instance.is_deleted:
        logger.info(f"Todo {instance.id} is marked as deleted.")
        # 無限ループ防止フラグ (削除処理用)
        if SYNC_FLAG.get("deleting_from_todo", False):
             logger.info(f"--- sync_from_todo (delete part) skipped for Todo ID: {instance.id} due to delete flag ---")
             return

        SYNC_FLAG["deleting_from_todo"] = True
        try:
            link = ScheduleTodoLink.objects.filter(todo=instance).first()
            if link:
                linked_schedule = link.schedule
                logger.info(f"Physically deleting Schedule {linked_schedule.id} linked to logically deleted Todo {instance.id}.")
                linked_schedule.delete()  # Scheduleを物理削除
            else:
                logger.info(f"No link found for logically deleted Todo {instance.id}. No Schedule deleted.")
            # 削除時は同期処理はスキップするためここで return
            logger.info(f"--- sync_from_todo (delete part) finished for Todo ID: {instance.id} ---")
            return
        except Exception as e:
            logger.error(f"Error during delete sync from Todo {instance.id}: {e}", exc_info=True)
        finally:
            SYNC_FLAG["deleting_from_todo"] = False
            # 削除処理が終わったらここで終了
            return

    # 通常の保存処理 (論理削除でない場合)
    SYNC_FLAG["from_todo"] = True
    saved_schedule = None # 保存されたScheduleインスタンスを保持する変数
    link = None # Linkインスタンスを保持する変数
    try:
        link = ScheduleTodoLink.objects.filter(todo=instance).first()
        # 日本時刻に設定
        jst = pytz_timezone('Asia/Tokyo')
        # ★★★ expire_datetime が None の場合の処理を修正 ★★★
        dt = instance.expire_datetime.astimezone(jst) if instance.expire_datetime else None
        # 完了時刻に値が設定されているか
        complete_flug = bool(instance.finished_date) # finished_date があれば True

        if link:
            schedule = link.schedule
            logger.info(f"Found existing link for Todo {instance.id} to Schedule {schedule.id}.")
            schedule.summary = instance.item_name
            schedule.description = instance.description
            schedule.is_completed = complete_flug
            schedule.reminder_enabled = instance.reminder_todo_enabled
            if dt:
                schedule.date = dt.date()
                schedule.end_datetime = dt
                # ★★★ start_datetime も更新するか検討 (仕様による) ★★★
                # 現状 start_datetime は更新されない。もし同期が必要なら追加。
                # schedule.start_datetime = dt # 例: 終了時刻と同じにする場合
            else:
                # expire_datetime が None の場合の Schedule の日付・時刻をどうするか？
                # 例: 現在の日付にする、Noneにするなど仕様に応じて決定
                schedule.date = timezone.now().date() # 仮: 現在の日付
                schedule.end_datetime = None
                # schedule.start_datetime = None # 必要なら
            schedule.save()
            saved_schedule = schedule # 保存したインスタンスを保持
            logger.info(f"Updated Schedule {schedule.id} from Todo {instance.id}.")
        else:
            logger.info(f"No existing link found for Todo {instance.id}. Creating new Schedule and Link.")
            # 新規作成
            schedule_data = {
                'summary': instance.item_name,
                'description': instance.description,
                'user_id': instance.user.id, # Todo のユーザーを使用
                'is_completed': complete_flug,
                'reminder_enabled': instance.reminder_todo_enabled,
            }
            if dt:
                schedule_data['date'] = dt.date()
                schedule_data['end_datetime'] = dt
                # ★★★ start_datetime のデフォルト値を設定 ★★★
                schedule_data['start_datetime'] = dt # 仮: 終了時刻と同じにする
            else:
                # expire_datetime が None の場合のデフォルト値
                now_jst = timezone.now().astimezone(jst)
                schedule_data['date'] = now_jst.date()
                schedule_data['end_datetime'] = None
                # ★★★ start_datetime のデフォルト値を設定 ★★★
                schedule_data['start_datetime'] = now_jst # 仮: 現在時刻

            schedule = Schedule.objects.create(**schedule_data)
            # ★★★ Linker作成時に created_from を指定 ★★★
            link = ScheduleTodoLink.objects.create(
                schedule=schedule,
                todo=instance,
                created_from='todo' # Todoから作成された
            )
            saved_schedule = schedule # 保存したインスタンスを保持
            logger.info(f"Created new Schedule {schedule.id} and Link {link.id} from Todo {instance.id} (created_from='todo').")

        # ★★★ Schedule保存後に、作成元に基づいてリマインダー再スケジュール処理を呼び出す ★★★
        if saved_schedule and link: # saved_schedule と link の両方が存在することを確認
            if link.created_from == 'schedule':
                 logger.info(f"Calling reschedule_schedule_reminder for Schedule {saved_schedule.id} from sync_from_todo (created_from='schedule').")
                 # reschedule_schedule_reminder(saved_schedule) # ★★★ app側の関数を呼び出す (コメントアウト) ★★★
                 pass # app側の実装がまだなので pass
            else: # created_from == 'todo' の場合は何もしない (Todo側のリマインダーが担当)
               logger.info(f"Skipping reschedule_schedule_reminder for Schedule {saved_schedule.id} from sync_from_todo (created_from='todo').")
        elif saved_schedule:
            logger.warning(f"Link object was not available after saving Schedule {saved_schedule.id} in sync_from_todo. Skipping reschedule check.")
        else:
            logger.warning("Saved Schedule object was not available in sync_from_todo. Skipping reschedule check.")

    except Exception as e: # エラーハンドリングを追加
        logger.error(f"Error in sync_from_todo for Todo {instance.id}: {e}", exc_info=True)
    finally:
        SYNC_FLAG["from_todo"] = False
        logger.info(f"--- sync_from_todo finished for Todo ID: {instance.id} ---")
