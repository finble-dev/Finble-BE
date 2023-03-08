from django.apps import AppConfig
from django.conf import settings

class FinbleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finble'

    def ready(self):
        if settings.SCHEDULER_DEFAULT:
            from . import operator
            operator.start()
