# tenants/management/commands/cleanup_invitations.py

# Import django libraries
from django.core.management.base import BaseCommand
from django.utils import timezone

# Import third-party libraries
from django_tenants.utils import schema_context

# Import local modules
from tenants.models import UserInvitation


class Command(BaseCommand):
    help = "Deletes expired and unaccepted user invitations."

    def handle(self, *args, **kwargs):
        # Ensure we are operating on the public schema where invitations are stored
        with schema_context("public"):
            now = timezone.now()
            # Find invitations that have expired and were not accepted
            expired_invitations = UserInvitation.objects.filter(
                expires_at__lt=now, is_accepted=False
            )

            count = expired_invitations.count()

            if count > 0:
                expired_invitations.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted {count} expired invitations."
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS("No expired invitations found."))
