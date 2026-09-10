from django.apps import AppConfig


class AgencyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agency"

    def ready(self):
        from . import signals  # noqa: F401
