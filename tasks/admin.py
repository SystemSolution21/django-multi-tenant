# tasks/admin.py

# Import django libraries
from django.contrib import admin
from django.db import connection

# Import local modules
from core.admin import TimeStampedModelAdmin
from tasks.models import Project, Task
from tenants.models import User


class TenantUserFilter(admin.SimpleListFilter):
    """
    A generic filter for a User foreign key that is limited to
    users within the current tenant.
    """

    # This must be overridden by subclasses
    title = "user"
    parameter_name = "user"

    def lookups(self, request, model_admin):
        if connection.schema_name != "public":
            # Get users who are members of the current tenant
            users = User.objects.filter(tenants__schema_name=connection.schema_name)
            return [(u.pk, u.email) for u in users]
        return []

    def queryset(self, request, queryset):
        if self.value():
            # Use a dictionary to dynamically set the filter parameter
            filter_param = {f"{self.parameter_name}__id": self.value()}
            return queryset.filter(**filter_param)
        return queryset


class OwnerFilter(TenantUserFilter):
    title = "owner"
    parameter_name = "owner"


class ProjectAdmin(TimeStampedModelAdmin):
    """Admin class for the Project model."""

    list_display: list[str] = ["id", "key", "name", "owner", "created_at", "updated_at"]
    list_display_links: list[str] = ["id", "key", "name"]
    list_filter = [OwnerFilter]
    search_fields: list[str] = ["key", "name", "description"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            # Filter users to only those in the current tenant
            if connection.schema_name != "public":
                kwargs["queryset"] = User.objects.filter(
                    tenants__schema_name=connection.schema_name
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AssigneeFilter(TenantUserFilter):
    title = "assignee"
    parameter_name = "assignee"


class TaskAdmin(TimeStampedModelAdmin):
    """Admin class for the Task model."""

    list_display: list[str] = [
        "id",
        "name",
        "project",
        "assignee",
        "status",
        "priority",
        "due_date",
        "created_at",
        "updated_at",
    ]
    list_display_links: list[str] = ["id", "name"]
    list_filter = ["project", "status", "priority", AssigneeFilter]
    search_fields: list[str] = ["name", "description"]
    date_hierarchy: str = "due_date"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assignee":
            # Filter users to only those in the current tenant
            if connection.schema_name != "public":
                kwargs["queryset"] = User.objects.filter(
                    tenants__schema_name=connection.schema_name
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(model_or_iterable=Project, admin_class=ProjectAdmin)
admin.site.register(model_or_iterable=Task, admin_class=TaskAdmin)
