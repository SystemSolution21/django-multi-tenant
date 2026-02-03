# tenants/mixins.py

# Import standard libraries
from typing import TYPE_CHECKING

# Import django libraries
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import connection

# Import third-party libraries

if TYPE_CHECKING:
    from django.http import HttpRequest


class TenantAdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires user to be a tenant admin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # This mixin is for tenant-specific views. It should not be used on the public schema.
        # A global superuser will pass the check below, but this prevents misuse.
        if connection.schema_name == "public":
            raise PermissionDenied("This page is not accessible on the public domain.")

        # In a tenant schema, the `user.is_superuser` property from `django-tenant-users`
        # correctly checks for both global superuser status and tenant-specific
        # admin status (`UserTenantPermissions.is_superuser`). This single check is sufficient.
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(
            "You must be a tenant administrator to access this page."
        )


class TenantStaffRequiredMixin(UserPassesTestMixin):
    """Require user to be at least staff in tenant"""

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False

        # This mixin is for tenant-specific views.
        if connection.schema_name == "public":
            return False

        # The user.is_staff property from django-tenant-users handles both
        # global and tenant-specific staff checks. A global superuser is
        # also considered staff.
        return user.is_staff


class PublicSchemaRequiredMixin(UserPassesTestMixin):
    """Require access from public schema only"""

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        return connection.schema_name == "public"


class TenantSchemaRequiredMixin(UserPassesTestMixin):
    """Require access from tenant schema only"""

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        return connection.schema_name != "public"
