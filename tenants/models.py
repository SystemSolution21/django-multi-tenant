# tenants/models.py

# Import standard libraries
import uuid
from datetime import timedelta
from typing import Any, cast

# Import django libraries
from django.db import models, connection
from django.utils import timezone
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase, UserProfile

# Import local modules
from core.models import TimeStampedModel


class User(UserProfile):
    """
    Extended user model with additional fields.
    """

    @property
    def is_superuser(self) -> bool:
        """
        Override is_superuser to safely handle public schema checks.
        """
        # 1. Global superuser flag always wins.
        # We access the raw value from __dict__ to avoid recursion caused by the property shadowing the field.
        if self.__dict__.get("is_superuser", False):
            return True
        if self.is_global_superuser:
            return True

        # 2. If on public schema, we cannot check tenant permissions
        # because the table doesn't exist. Return False.
        if connection.schema_name == "public":
            return False

        # 3. Delegate to parent logic for tenant-specific checks
        return cast(bool, super().is_superuser)

    @is_superuser.setter
    def is_superuser(self, value: bool) -> None:
        self.__dict__["is_superuser"] = value

    @property
    def is_staff(self) -> bool:
        """
        Override is_staff to safely handle public schema checks.
        """
        if self.__dict__.get("is_staff", False):
            return True
        if self.is_global_staff:
            return True
        if connection.schema_name == "public":
            return False
        return cast(bool, super().is_staff)

    @is_staff.setter
    def is_staff(self, value: bool) -> None:
        self.__dict__["is_staff"] = value

    def has_perm(self, perm: str, obj: Any | None = None) -> bool:
        """
        Override has_perm to safely handle public schema checks.
        A global superuser always has all permissions.
        """
        if self.__dict__.get("is_superuser", False):
            return True
        if self.is_global_superuser:
            return True
        if connection.schema_name == "public":
            return False
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label: str) -> bool:
        """
        Override has_module_perms to safely handle public schema checks.
        A global superuser always has all permissions.
        """
        if self.__dict__.get("is_superuser", False):
            return True
        if self.is_global_superuser:
            return True
        if connection.schema_name == "public":
            return False
        return super().has_module_perms(app_label)

    ROLE_CHOICES: list[tuple[str, str]] = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("user", "Regular User"),
    ]

    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_global_superuser = models.BooleanField(
        default=False,
        help_text="Designates that this user has all permissions across all tenants.",
    )
    is_global_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the admin site.",
    )

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"  # type: ignore[attr-defined]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Tenant(TenantBase, TimeStampedModel):
    name = models.CharField(max_length=100)

    def add_user(self, user_obj, is_superuser=False, is_staff=False):
        """
        Override add_user to skip creating UserTenantPermissions for the public tenant,
        as the table does not exist in the public schema.
        """
        if self.schema_name == "public":
            return None
        return super().add_user(user_obj, is_superuser=is_superuser, is_staff=is_staff)

    def remove_user(self, user_obj):
        """
        Override remove_user to skip removing UserTenantPermissions for the public tenant.
        """
        if self.schema_name == "public":
            return None
        return super().remove_user(user_obj)


class Domain(DomainMixin, TimeStampedModel):
    pass


class UserInvitation(TimeStampedModel):
    """Model for user invitations to tenants"""

    ROLE_CHOICES: list[tuple[str, str]] = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("user", "Regular User"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    invited_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = (("tenant", "email"),)

    def save(self, *args, **kwargs) -> None:
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation for {self.email} to {self.tenant.name}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
