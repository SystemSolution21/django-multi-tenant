# tenants/management/commands/cleanup_orphaned_users.py

# Import django libraries
from django.core.management.base import BaseCommand

# Import third-party libraries
from django_tenants.utils import schema_context

# Import local modules
from tenants.models import User


class Command(BaseCommand):
    help = "Deletes users who are not assigned to any tenant (orphaned users)."

    def handle(self, *args, **kwargs):
        # Ensure we are operating on the public schema
        with schema_context("public"):
            # Find users who are not associated with any tenant
            # We exclude superusers to prevent accidental lockout if they were created manually without a tenant
            orphaned_users = User.objects.filter(
                tenants__isnull=True, is_superuser=False
            )

            count = orphaned_users.count()

            if count > 0:
                orphaned_users.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deleted {count} orphaned users.")
                )
            else:
                self.stdout.write(self.style.SUCCESS("No orphaned users found."))
