# tasks/admin.py

# Import django libraries
from django.contrib import admin

# Import local modules
from core.admin import TimeStampedModelAdmin
from tasks.models import Project, Task


class ProjectAdmin(TimeStampedModelAdmin):
    """Admin class for the Project model."""

    list_display: list[str] = ["id", "key", "name", "owner", "created_at", "updated_at"]
    list_display_links: list[str] = ["id", "key", "name"]
    list_filter: list[str] = ["owner"]
    search_fields: list[str] = ["key", "name", "description"]


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
    list_filter: list[str] = ["project", "status", "priority", "assignee"]
    search_fields: list[str] = ["name", "description"]
    date_hierarchy: str = "due_date"


admin.site.register(model_or_iterable=Project, admin_class=ProjectAdmin)
admin.site.register(model_or_iterable=Task, admin_class=TaskAdmin)
