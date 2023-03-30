from django.apps import AppConfig
from django.conf import settings


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'

    def ready(self):
        if not settings.DEBUG:
            from scheduler import tasks
            tasks.run()
