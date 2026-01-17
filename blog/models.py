# blog/models.py

# Import django libraries
from django.db import models

# Import local modules
from core.models import TimeStampedModel


class Article(TimeStampedModel):
    """
    A blog article model.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self) -> str:
        return f"{self.title}"
