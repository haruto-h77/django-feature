
from __future__ import absolute_import, unicode_literals

# Celeryアプリケーションを読み込む
from .celery import app as celery_app

__all__ = ('celery_app',)
