# tenants/admin.py

# Import standard libraries
from typing import Any, Literal, cast

# Import django libraries
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import ProgrammingError, connection, models
from django_tenants.admin import TenantAdminMixin
from django_tenants.utils import schema_context

# Import local modules
from tenants.models import Domain, Tenant, User
from tasks.models import Project, Task


def table_exists(table_name) -> Any | Literal[False]:
    """
    Check if a table exists in the current schema.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            sql="""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_name = %s
            )
            """,
            params=[table_name],
        )
        result: tuple[Any, ...] | None = cursor.fetchone()
        return result[0] if result else False


class UserAdminForm(forms.ModelForm):
    is_staff = forms.BooleanField(
        label="Is staff",
        required=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_superuser = forms.BooleanField(
        label="Is superuser",
        required=False,
        help_text="Designates that this user has all permissions without explicitly assigning them.",
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["is_staff"].initial = self.instance.is_staff
            self.fields["is_superuser"].initial = self.instance.is_superuser

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = self.cleaned_data["is_superuser"]
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin class for the User model."""

    form = UserAdminForm

    list_display: list[str] = ["id", "email", "role", "is_tenant_admin", "is_active"]
    list_display_links: list[str] = ["id", "email"]
    search_fields: list[str] = ["email", "first_name", "last_name"]
    list_filter: list[str] = ["role", "is_tenant_admin", "is_active"]
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
                    "is_staff",
                    "is_superuser",
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

    def get_readonly_fields(self, request, obj=None) -> list[str]:
        if request.user.is_superuser:
            return []
        return ["is_staff", "is_superuser"]

    def delete_model(self, request, obj: User) -> None:
        # Cancel the delete if the user owns any tenant
        if Tenant.objects.filter(owner=obj).exists():
            raise ValidationError(
                message="You cannot delete a user that is a tenant owner."
            )

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
                    if table_exists(table_name=Project._meta.db_table):
                        Project.objects.filter(owner=obj).update(owner=None)
                    if table_exists(table_name=Task._meta.db_table):
                        Task.objects.filter(assignee=obj).update(assignee=None)
                except ProgrammingError:
                    # This can happen if the tables don't exist in a particular
                    # schema, which is unlikely but possible in complex setups
                    # or during migrations. We can safely ignore it.
                    pass

        # Temporarily disable on_delete behavior for tenant-specific models
        # to prevent Django from trying to update non-existent tables in public schema.
        project_owner_field: models.ForeignKey[Any] = cast(
            models.ForeignKey, Project._meta.get_field(field_name="owner")
        )
        task_assignee_field: models.ForeignKey[Any] = cast(
            models.ForeignKey, Task._meta.get_field(field_name="assignee")
        )

        original_project_on_delete: Any = project_owner_field.on_delete  # type: ignore
        original_task_on_delete: Any = task_assignee_field.on_delete  # type: ignore

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

    list_display: list[str] = ["id", "name", "schema_name", "created_at"]
    list_display_links: list[str] = ["id", "name"]
    search_fields: list[str] = ["name", "schema_name"]

    def delete_model(self, request, obj) -> None:
        # Force delete the tenant
        obj.delete_tenant()


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display: list[str] = ["id", "domain", "tenant", "is_primary"]
    list_display_links: list[str] = ["id", "domain"]
    search_fields: list[str] = ["domain"]
