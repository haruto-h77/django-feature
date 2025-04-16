from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from app.models import Schedule
from todo.models import Todo
from .models import ScheduleTodoLink
from datetime import datetime
from django.utils import timezone

# 無限ループ対応
__sync_flag = {"from_schedule": False, "from_todo": False}

# Schedule側でpost_saveされた場合
@receiver(post_save, sender=Schedule)
def sync_from_schedule(sender, instance, created, **kwargs):
    if __sync_flag["from_todo"]:
        return

    __sync_flag["from_schedule"] = True
    try:
        link = ScheduleTodoLink.objects.filter(schedule=instance).first()
        if link:
            todo = link.todo
            todo.item_name = instance.summary
            todo.description = instance.description
            todo.expire_datetime = timezone.make_aware(datetime.combine(instance.date, instance.end_time))
            todo.save()
        else:
            todo = Todo.objects.create(
                user_id=instance.user_id,
                item_name=instance.summary,
                description=instance.description,
                registration_date=instance.created_at,
                expire_datetime=timezone.make_aware(datetime.combine(instance.date, instance.end_time)),
            )
            ScheduleTodoLink.objects.create(schedule=instance, todo=todo)
    finally:
        __sync_flag["from_schedule"] = False

# Schedule側でpre_deleteされた場合
@receiver(pre_delete, sender=Schedule)
def sync_delete_from_schedule(sender, instance, **kwargs):
    links = ScheduleTodoLink.objects.filter(schedule=instance)
    if not links.exists():
        return
    # linkerが存在していた場合はtodoを論理削除 linker自体はSchdule側の物理削除で削除される
    for link in links:
        linked_todo = link.todo
        linked_todo.is_deleted = True  # 論理削除
        linked_todo.save()

# Todo側でpost_saveされた場合
@receiver(post_save, sender=Todo)
def sync_from_todo(sender, instance, created, **kwargs):
    if __sync_flag["from_schedule"]:
        return

    # 論理削除時の処理
    if instance.is_deleted:
        if __sync_flag["from_todo"]:
            return
        
        __sync_flag["from_todo"] = True
        try:
            link = ScheduleTodoLink.objects.filter(todo=instance).first()
            if link:
                linked_schedule = link.schedule
                linked_schedule.delete()  # Scheduleを物理削除
            return  # 同期処理はスキップする
        finally:
            __sync_flag["from_todo"] = False

    __sync_flag["from_todo"] = True
    try:
        link = ScheduleTodoLink.objects.filter(todo=instance).first()
        if link:
            schedule = link.schedule
            schedule.summary = instance.item_name
            schedule.description = instance.description
            if instance.expire_datetime:
                schedule.date = instance.expire_datetime.date()
                schedule.end_time = instance.expire_datetime.time()
            schedule.save()
        else:
            if instance.expire_datetime:
                schedule = Schedule.objects.create(
                    summary=instance.item_name,
                    description=instance.description,
                    date=instance.expire_datetime.date(),
                    end_time=instance.expire_datetime.time(),
                    user_id=instance.user.id,
                )
            else:
                schedule = Schedule.objects.create(
                    summary=instance.item_name,
                    description=instance.description,
                    date=timezone.now().date(),
                    end_time=datetime.time(7, 0, 0),
                    user_id=instance.user.id,
                )
            ScheduleTodoLink.objects.create(schedule=schedule, todo=instance)
    finally:
        __sync_flag["from_todo"] = False
