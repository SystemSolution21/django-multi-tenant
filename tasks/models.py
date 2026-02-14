# tasks/models.py

# Import django libraries
from django.db import models
from django.utils import timezone

# Import local modules
from core.models import TimeStampedModel
from tenants.models import User


class Project(TimeStampedModel):
    """
    A project model.
    """

    # Attributes
    key = models.CharField(
        max_length=5, help_text="Short key for identifying the project", unique=True
    )
    name = models.CharField(max_length=255, help_text="Project's full name")
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="owned_projects"
    )

    class Meta:
        indexes = [
            models.Index(fields=["key"], name="project_key_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"


class Task(TimeStampedModel):
    """
    A task model.
    """

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    ]
    PRIORITY_CHOICES: list[tuple[str, str]] = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    # Attributes
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE, related_name="tasks"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    due_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="task_status_idx"),
            models.Index(fields=["assignee"], name="task_assignee_idx"),
        ]

    def save(self, *args, **kwargs) -> None:
        # Auto-sync is_done with status
        self.is_done = self.status == "done"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self) -> bool:
        if self.due_date and not self.is_done:
            return self.due_date < timezone.now().date()
        return False

    def __str__(self) -> str:
        return f"[{self.project.key}-{self.pk}] {self.name}"
