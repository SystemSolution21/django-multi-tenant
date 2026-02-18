# tenants/management/commands/init_public_tenant.py

# Import standard libraries
import os

# Import django libraries
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

# Import local modules
from tenants.models import Domain, Tenant, User


class Command(BaseCommand):
    help = "Initialize public tenant if it does not exist."

    def handle(self, *args, **options):
        # Check if public tenant already exists
        if Tenant.objects.filter(schema_name=settings.PUBLIC_SCHEMA_NAME).exists():
            self.stdout.write("Public tenant already exists. Skipping initialization.")
            return

        self.stdout.write("Creating public tenant...")

        # Configuration for the default public admin
        email = os.getenv("PUBLIC_TENANT_ADMIN_EMAIL", "admin@lvh.me")
        password = os.getenv("PUBLIC_TENANT_ADMIN_PASSWORD", "password")
        domain_url = getattr(settings, "BASE_DOMAIN", "lvh.me")

        try:
            with transaction.atomic():
                # 1. Create public tenant owner
                # We manually create the user to ensure they are set as global superuser
                public_owner = User.objects.create(
                    email=email,
                    is_active=True,
                    is_verified=True,
                    role="admin",
                    is_global_superuser=True,
                    is_global_staff=True,
                )
                public_owner.set_password(password)
                public_owner.save()

                # 2. Create the public tenant instance
                public_tenant = Tenant.objects.create(
                    schema_name=settings.PUBLIC_SCHEMA_NAME,
                    name="Public Tenant",
                    owner=public_owner,
                    slug="public",
                )

                # 3. Create the domain for the public tenant
                Domain.objects.create(
                    domain=domain_url, tenant=public_tenant, is_primary=True
                )

                # Add localhost for development convenience
                if settings.DEBUG and domain_url != "localhost":
                    Domain.objects.get_or_create(
                        domain="localhost",
                        tenant=public_tenant,
                        defaults={"is_primary": False},
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully initialized public tenant.\nAdmin: {email}\nPassword: {password}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to initialize public tenant: {e}")
            )
