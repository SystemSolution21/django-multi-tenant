# tasks/models.py

# Import django libraries
from django.db import models

# Import local modules
from core.models import TimeStampedModel


class Project(TimeStampedModel):
    """
    A project model.
    """

    # Attributes
    key = models.CharField(
        max_length=5, help_text="Short key for identifying the project"
    )
    name = models.CharField(max_length=255, help_text="Project's full name")
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["key"], name="project_key_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"


class Task(TimeStampedModel):
    """
    A task model.
    """

    # Attributes
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(
        to=Project, on_delete=models.CASCADE, related_name="tasks"
    )
    is_done = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"[{self.project.key}-{self.pk}] {self.name}"
