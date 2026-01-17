# tasks/admin.py

# Import django libraries
from django.contrib import admin

# Import local modules
from core.admin import TimeStampedModelAdmin
from tasks.models import Project, Task


class ProjectAdmin(TimeStampedModelAdmin):
    """Admin class for the Project model."""

    list_display: list[str] = ["id", "key", "name", "created_at", "updated_at"]
    list_display_links: list[str] = ["id", "key", "name"]


class TaskAdmin(TimeStampedModelAdmin):
    """Admin class for the Task model."""

    list_display: list[str] = [
        "id",
        "name",
        "project",
        "is_done",
        "created_at",
        "updated_at",
    ]
    list_display_links: list[str] = ["id", "name"]
    list_filter: list[str] = ["project", "is_done"]
    search_fields: list[str] = ["name", "description"]


admin.site.register(model_or_iterable=Project, admin_class=ProjectAdmin)
admin.site.register(model_or_iterable=Task, admin_class=TaskAdmin)
