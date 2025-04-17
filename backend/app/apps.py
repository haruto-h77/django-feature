from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'backend.app'

    def ready(self):
        import backend.app.signals  # signalsを読み込ませる！
