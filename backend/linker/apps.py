from django.apps import AppConfig

class LinkerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.linker'

    def ready(self):
        import backend.linker.signals  # signals.py を読み込む
