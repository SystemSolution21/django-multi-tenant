# tenants/admin.py

# Import standard libraries
from typing import cast

# Import django libraries
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import ProgrammingError, connection, models
from django_tenants.admin import TenantAdminMixin
from django_tenants.utils import schema_context

# Import local modules
from tenants.models import Domain, Tenant, User
from tasks.models import Project, Task


def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_name = %s
            )
            """,
            [table_name],
        )
        result = cursor.fetchone()
        return result[0] if result else False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin class for the User model."""

    list_display = ["id", "email", "role", "is_tenant_admin", "is_active"]
    list_display_links = ["id", "email"]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["role", "is_tenant_admin", "is_active"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "email",
                    "password",
                ],
            },
        ),
        (
            "Personal Info",
            {
                "fields": [
                    "first_name",
                    "last_name",
                    "phone",
                ],
            },
        ),
        (
            "Permissions",
            {
                "fields": [
                    "role",
                    "is_tenant_admin",
                    "is_active",
                    "is_verified",
                ],
            },
        ),
        (
            "Important dates",
            {
                "fields": [
                    "last_login",
                ],
            },
        ),
    ]

    def delete_model(self, request, obj: User) -> None:
        # Cancel the delete if the user owns any tenant
        if Tenant.objects.filter(owner=obj).exists():
            raise ValidationError("You cannot delete a user that is a tenant owner.")

        # Before deleting the user, we must manually clean up any ForeignKeys
        # from tenant-specific models that point to this user.
        # Django's default delete collector runs in the 'public' schema and
        # cannot see the tables in tenant schemas. We must iterate through ALL
        # tenants, not just the ones the user belongs to, because the user
        # might have been removed from a tenant but objects they created could
        # still reference them.
        all_tenants = Tenant.objects.exclude(schema_name="public")
        for tenant in all_tenants:
            with schema_context(tenant.schema_name):
                try:
                    # Nullify the 'owner' field for Projects and 'assignee' for Tasks
                    if table_exists(Project._meta.db_table):
                        Project.objects.filter(owner=obj).update(owner=None)
                    if table_exists(Task._meta.db_table):
                        Task.objects.filter(assignee=obj).update(assignee=None)
                except ProgrammingError:
                    # This can happen if the tables don't exist in a particular
                    # schema, which is unlikely but possible in complex setups
                    # or during migrations. We can safely ignore it.
                    pass

        # Temporarily disable on_delete behavior for tenant-specific models
        # to prevent Django from trying to update non-existent tables in public schema.
        project_owner_field = cast(models.ForeignKey, Project._meta.get_field("owner"))
        task_assignee_field = cast(models.ForeignKey, Task._meta.get_field("assignee"))

        original_project_on_delete = project_owner_field.on_delete  # type: ignore
        original_task_on_delete = task_assignee_field.on_delete  # type: ignore

        try:
            # Tell the collector to do nothing for these relationships.
            # We've already handled the data cleanup in the loop above.
            project_owner_field.on_delete = models.DO_NOTHING  # type: ignore[misc]
            task_assignee_field.on_delete = models.DO_NOTHING  # type: ignore[misc]
            # Now, this deletion will succeed from the public schema.
            User.objects.delete_user(obj)  # type: ignore[call-arg]
        finally:
            # Always restore the original on_delete behavior.
            project_owner_field.on_delete = original_project_on_delete  # type: ignore[misc]
            task_assignee_field.on_delete = original_task_on_delete  # type: ignore[misc]


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin class for the Tenant model."""

    list_display = ["id", "name", "schema_name", "created_at"]
    list_display_links = ["id", "name"]
    search_fields = ["name", "schema_name"]

    def delete_model(self, request, obj) -> None:
        # Force delete the tenant
        obj.delete_tenant()


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display = ["id", "domain", "tenant", "is_primary"]
    list_display_links = ["id", "domain"]
    search_fields = ["domain"]
