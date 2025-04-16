from django.apps import AppConfig

class LinkerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'linker'

    def ready(self):
        import linker.signals  # signals.py を読み込む
