from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tenants.models import Tenant, User
from tenant_users.permissions.models import UserTenantPermissions
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Demote a user from superuser and assign tenant-specific permissions."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to update")
        parser.add_argument("schema_name", type=str, help="Schema name of the tenant")
        parser.add_argument(
            "--set-tenant-admin",
            action="store_true",
            help="Set tenant-specific is_superuser and is_staff to True",
        )
        parser.add_argument(
            "--set-tenant-regular",
            action="store_true",
            help="Set tenant-specific is_superuser to False and is_staff to True (for regular users)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow demoting a global superuser. Use with caution.",
        )

    def handle(self, *args, **options):
        email = options["email"]
        schema_name = options["schema_name"]
        set_tenant_admin = options["set_tenant_admin"]
        set_tenant_regular = options["set_tenant_regular"]
        force = options["force"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User "{email}" does not exist')

        # Add a safeguard to prevent accidental demotion of a global superuser
        if user.is_superuser and not force:
            raise CommandError(
                f'User "{email}" is a global superuser. '
                "This command is intended for tenant users. "
                "Use --force to override this safeguard."
            )
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant "{schema_name}" does not exist')

        # 1. Update Global User properties
        # Use update() to modify the DB columns directly, bypassing the read-only properties.
        # We set is_global_superuser=False (demote global admin) and is_global_staff=True (allow admin access).
        User.objects.filter(pk=user.pk).update(
            is_global_superuser=False, is_global_staff=True
        )

        # Update the role based on the command flags
        if set_tenant_admin:
            user.role = "admin"
        elif set_tenant_regular:
            user.role = "user"

        # Only update the role field to avoid overwriting the is_superuser/is_staff changes
        user.save(update_fields=["role"])
        self.stdout.write(
            "Global User updated: is_global_superuser=False, is_global_staff=True (Demoted from Global Admin)"
        )

        # 2. Assign specific permissions INSIDE the tenant context
        with schema_context(tenant.schema_name):
            utp = UserTenantPermissions.objects.get(profile=user)

            if set_tenant_admin:
                utp.is_superuser = True
                utp.is_staff = True
                utp.user_permissions.clear()  # Clear specific permissions if they are a tenant superuser
                self.stdout.write(
                    f"Tenant Permissions: Set '{email}' as ADMIN for tenant '{schema_name}'."
                )
            else:  # This covers both --set-tenant-regular and the default case
                utp.is_superuser = False
                utp.is_staff = True
                # Assign specific permissions for the Tasks app INSIDE the tenant context
                project_ct = ContentType.objects.get(app_label="tasks", model="project")
                task_ct = ContentType.objects.get(app_label="tasks", model="task")
                permissions = Permission.objects.filter(
                    content_type__in=[project_ct, task_ct]
                )
                utp.user_permissions.set(permissions)

                if set_tenant_regular:
                    self.stdout.write(
                        f"Tenant Permissions: Set '{email}' as REGULAR USER for tenant '{schema_name}' with Task/Project permissions."
                    )
                else:  # Default case message
                    self.stdout.write(
                        f"Tenant Permissions (Default): Set '{email}' as REGULAR USER for tenant '{schema_name}' with Task/Project permissions."
                    )

            utp.save()

            self.stdout.write(
                self.style.SUCCESS(f"Permissions updated for {email} in {schema_name}")
            )
