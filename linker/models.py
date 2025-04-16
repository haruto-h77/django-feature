from django.db import models

class ScheduleTodoLink(models.Model):
    schedule = models.ForeignKey('app.Schedule', on_delete=models.CASCADE, related_name='linked_todos')
    todo = models.ForeignKey('todo.Todo', on_delete=models.CASCADE, related_name='linked_schedules')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.schedule.summary} ↔ {self.todo.item_name}"
