# tenants/models.py

# Import django libraries
import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

# Import third-party libraries
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase, UserProfile

# Import local modules
from core.models import TimeStampedModel


class User(UserProfile):
    """
    Extended user model with additional fields.
    """

    ROLE_CHOICES: list[tuple[str, str]] = [
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("user", "Regular User"),
    ]

    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    is_tenant_admin = models.BooleanField(default=False)

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.email} ({role_display})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Tenant(TenantBase, TimeStampedModel):
    """
    A tenant model.
    """

    name = models.CharField(max_length=100)


class Domain(DomainMixin, TimeStampedModel):
    """
    A domain model.
    """

    pass


class UserInvitation(TimeStampedModel):
    """
    Model to handle user invitations to tenants.
    """

    email = models.EmailField()
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=User.ROLE_CHOICES, default="user")
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Invitation for {self.email} to {self.tenant.name}"
