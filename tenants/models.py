# tenants/models.py

# Import django libraries
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

# Import local modules
from core.models import TimeStampedModel


class User(AbstractUser):
    pass


class Tenant(TenantMixin, TimeStampedModel):
    name = models.CharField(max_length=100)


class Domain(DomainMixin, TimeStampedModel):
    pass
