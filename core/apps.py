# core/apps.py

# Import django libraries
from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    """
    Custom admin config to use the custom admin site.
    """

    default_site = "core.sites.TenantAdminSite"
