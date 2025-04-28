from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta, datetime
from django.utils import timezone
from .models import Schedule
import logging
from backend.linker.models import ScheduleTodoLink # Linkerモデルをインポート

logger = logging.getLogger(__name__)

@shared_task
def send_reminder(schedule_id):
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        
        try:
            link = ScheduleTodoLink.objects.filter(schedule=schedule).first()
            # Linkerが存在し、かつ作成元が 'todo' だった場合は送信しない
            if link and link.created_from == 'todo':
                logger.info(f"Skipping Schedule reminder for {schedule_id} because it was originally created from Todo.")
                # ★★★ 念のため、関連するTodo側のタスクIDもクリアしておく (必須ではない) ★★★
                # if schedule.reminder_task_id:
                #     schedule.reminder_task_id = None
                #     # シグナル経由せずに直接保存
                #     Schedule.objects.filter(id=schedule_id).update(reminder_task_id=None)
                return
            # Linkerが存在しない場合、または作成元が 'schedule' の場合は続行
            elif link:
                 logger.info(f"Proceeding with Schedule reminder for {schedule_id} as it was originally created from Schedule.")
            else:
                 logger.info(f"Proceeding with Schedule reminder for {schedule_id} as it is not linked.")

        except Exception as e:
            # Linkerチェックでエラーが発生した場合、安全のため送信しない
            logger.error(f"Error checking linker origin for Schedule {schedule_id}: {e}", exc_info=True)
            return
        
        if not schedule.reminder_enabled:
            logger.info(f"Reminder is disabled for Schedule {schedule_id}. Reminder not sent.")
            return # リマインダー無効なら終了
        
        if schedule.is_completed:
            logger.info(f"Schedule {schedule_id} is already completed. Reminder not sent.")
            return # 完了済みの場合はメールを送らずに終了
        
        start_datetime_local = timezone.localtime(schedule.start_datetime)
        end_datetime_local = timezone.localtime(schedule.end_datetime)
        
        datetime_format = "%Y年%m月%d日 %H時%M分"
        start_datetime_str =  start_datetime_local.strftime(datetime_format)  # %-H, %-Mでゼロ埋めを省略
        end_datetime_str =  end_datetime_local.strftime(datetime_format)
        
        # メール本文をカスタマイズ
        message = (
            f"予定名: {schedule.summary}\n"
            f"説明: {schedule.description}\n"
            f"予定開始日時: {start_datetime_str}\n"
            f"予定終了日時: {end_datetime_str}\n\n"
        )
        
        # メールを送信
        send_mail(
            f"Reminder: {schedule.summary}",  # 件名
            message,  # 本文
            'from@example.com',  # 送信元
            ['to@example.com'],  # 送信先
            fail_silently=False,
        )
    except Schedule.DoesNotExist:
        logger.warning(f"Schedule with id {schedule_id} does not exist. Reminder not sent.")
