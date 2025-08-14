from django.apps import AppConfig


class LearningPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning_platform'
    verbose_name = 'Платформа обучения'

    def ready(self):
        import learning_platform.signals
