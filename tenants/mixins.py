# tenants/mixins.py

# Import standard libraries
from typing import TYPE_CHECKING

# Import django libraries
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import connection

# Import third-party libraries
from tenant_users.permissions.models import UserTenantPermissions

if TYPE_CHECKING:
    from django.http import HttpRequest


class TenantAdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires user to be a tenant admin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 1. Global Superuser always has access
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # 2. Check Tenant-Specific Permissions
        # We query the UserTenantPermissions table to see if this user
        # has admin rights (is_superuser=True) for the CURRENT tenant.
        try:
            utp = UserTenantPermissions.objects.get(profile=request.user)
            if utp.is_superuser:
                return super().dispatch(request, *args, **kwargs)
        except UserTenantPermissions.DoesNotExist:
            pass

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

        if user.is_superuser:
            return True

        try:
            utp = UserTenantPermissions.objects.get(profile=user)
            return utp.is_staff
        except UserTenantPermissions.DoesNotExist:
            return False


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
