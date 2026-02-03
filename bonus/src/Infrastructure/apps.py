from django.apps import AppConfig


class BonusConfig(AppConfig):
    """Django app configuration for the Bonus module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "bonus.src.Infrastructure"
    label = "bonus"
    verbose_name = "Bonus Module"
