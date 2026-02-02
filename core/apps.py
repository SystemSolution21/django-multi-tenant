# core/apps.py

# Import django libraries
from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig as BaseAdminConfig


class CoreConfig(AppConfig):
    name = "core"


class CustomAdminConfig(BaseAdminConfig):
    """
    Custom admin config to use the custom admin site.
    """

    default_site = "core.sites.TenantAdminSite"
