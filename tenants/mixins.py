# tenants/mixins.py

# Import standard libraries
from typing import TYPE_CHECKING

# Import django libraries
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import connection

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import User


class TenantAdminRequiredMixin(LoginRequiredMixin):
    """Mixin that requires user to be a tenant admin"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user is tenant admin or superuser
        user = request.user
        is_tenant_admin = getattr(user, "is_tenant_admin", False)
        if not (is_tenant_admin or user.is_superuser):
            raise PermissionDenied(
                "You must be a tenant administrator to access this page."
            )

        return super().dispatch(request, *args, **kwargs)


class TenantStaffRequiredMixin(UserPassesTestMixin):
    """Require user to be at least staff in tenant"""

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        user: "User" = self.request.user  # type: ignore[assignment]
        return user.is_authenticated and user.role in ["admin", "staff"]


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
