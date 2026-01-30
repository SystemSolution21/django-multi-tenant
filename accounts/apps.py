# accounts/apps.py

# Import django libraries
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field: str = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self) -> None:
        pass
