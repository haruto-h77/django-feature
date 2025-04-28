from django.db import models

class ScheduleTodoLink(models.Model):
    schedule = models.ForeignKey('app.Schedule', on_delete=models.CASCADE, related_name='linked_todos')
    todo = models.ForeignKey('todo.Todo', on_delete=models.CASCADE, related_name='linked_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    created_from = models.CharField(
        max_length=10,
        choices=[('schedule', 'Schedule'), ('todo', 'Todo')],
        null=False, # 必須フィールド
        blank=False,
        editable=False, # 作成後は変更しない
        db_index=True,
        help_text='最初に作成された元のアプリ',
        default='schedule'
    )

    def __str__(self):
        return f"{self.schedule.summary} ↔ {self.todo.item_name}"
