# project/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Djangoのsettingsモジュールを設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.project.settings')

# Celeryアプリケーションのインスタンスを作成
app = Celery('project')

# Django設定をCeleryに読み込ませる
app.config_from_object('django.conf:settings', namespace='CELERY')

# タスクを自動的に検出する
app.autodiscover_tasks()

# Celeryインスタンスを返す
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
