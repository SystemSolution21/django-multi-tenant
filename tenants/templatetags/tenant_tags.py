# tenants/templatetags/tenant_tags.py

# Import django libraries
from django import template
from django.db import connection

# Import third-party libraries
from tenant_users.permissions.models import UserTenantPermissions

# Register the template library
register = template.Library()


@register.simple_tag(takes_context=True)
def is_tenant_admin(context):
    """
    Checks if the user in the current context is an admin for the current tenant.
    Returns True if the user is a global superuser or has the 'is_superuser'
    flag in the UserTenantPermissions model for the current tenant schema.
    """
    user = context.get("user")

    # User must be authenticated to be an admin
    if not user or not user.is_authenticated:
        return False

    # Global superusers are always admins
    if user.is_superuser:
        return True

    # This check is only relevant for tenant-specific schemas
    if connection.schema_name == "public":
        return False

    # Check for tenant-specific admin permissions
    utp = UserTenantPermissions.objects.filter(profile=user).first()
    return utp.is_superuser if utp else False
