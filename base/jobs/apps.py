from django.apps import AppConfig


class JobConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "base.jobs"

    def ready(self):
        import base.jobs.signals  # Import signals
