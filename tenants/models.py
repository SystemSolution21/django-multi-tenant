# tenants/models.py

# Import django libraries
from django.db import models

# Import third-party libraries
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase, UserProfile

# Import local modules
from core.models import TimeStampedModel


class User(UserProfile):
    """
    A user model.
    """

    pass


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
