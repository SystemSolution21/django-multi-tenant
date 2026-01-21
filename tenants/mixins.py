# tenants/mixins.py

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import connection

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import User


class TenantAdminRequiredMixin(UserPassesTestMixin):
    """Require user to be tenant admin"""

    if TYPE_CHECKING:
        request: HttpRequest

    def test_func(self) -> bool:
        user: "User" = self.request.user  # type: ignore[assignment]
        return user.is_authenticated and (user.is_tenant_admin or user.role == "admin")


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
