from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "authentication"
    name = "kot7k.authentication"
    verbose_name = "Authentication"

    def ready(self):
        from . import signals  # noqa: F401
