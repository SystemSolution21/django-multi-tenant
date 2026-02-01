from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tenants.models import Tenant
from tenant_users.permissions.models import UserTenantPermissions
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Demote a user from superuser and assign tenant-specific permissions."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to update")
        parser.add_argument("schema_name", type=str, help="Schema name of the tenant")

    def handle(self, *args, **options):
        email = options["email"]
        schema_name = options["schema_name"]
        User = get_user_model()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User "{email}" does not exist')

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant "{schema_name}" does not exist')

        # 1. Remove Global Superuser status
        user.is_superuser = False
        user.is_staff = True  # Required to access /admin/
        user.save()
        self.stdout.write("Global User updated: is_superuser=False, is_staff=True")

        # 2. Assign specific permissions INSIDE the tenant context
        with schema_context(tenant.schema_name):
            # Get content types for your models
            project_ct = ContentType.objects.get(app_label="tasks", model="project")
            task_ct = ContentType.objects.get(app_label="tasks", model="task")

            # Get permissions
            permissions = Permission.objects.filter(
                content_type__in=[project_ct, task_ct]
            )

            utp = UserTenantPermissions.objects.get(profile=user)
            utp.user_permissions.set(permissions)

            # Ensure tenant-level flags are also correct (if your model supports them)
            if hasattr(utp, "is_superuser"):
                utp.is_superuser = False
                utp.is_staff = True
                utp.save()

            self.stdout.write(
                self.style.SUCCESS(f"Permissions updated for {email} in {schema_name}")
            )
