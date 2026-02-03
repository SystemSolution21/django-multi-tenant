# tenants/templatetags/tenant_tags.py

# Import django libraries
from django import template
from django.db import connection

# Import third-party libraries

# Register the template library
register = template.Library()


@register.simple_tag(takes_context=True)
def is_tenant_admin(context):
    """Checks the user in the current context is an admin for the current tenant.
    Returns:
    True -  Users with is_superuser in the current tenant admins.
    False - Public schema superusers.
    False - None users or non-authenticated users.
    """
    user = context.get("user")

    # User must be authenticated to be an admin
    if not user or not user.is_authenticated:
        return False

    # On the public schema, the concept of a "tenant admin" doesn't apply.
    # Accessing `user.is_superuser` here would crash because it tries to
    # look up a permissions table that only exists in tenant schemas.
    if connection.schema_name == "public":
        return False

    # In a tenant schema, the `user.is_superuser` property from `django-tenant-users`
    # correctly checks for both global superuser status and tenant-specific
    # admin status. This single check is sufficient.
    return user.is_superuser
