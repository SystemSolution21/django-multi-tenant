# blog/tenant_specific_models.py

# Import django libraries
from django.db import models
from django.utils.text import slugify
from django.utils import timezone

# Import local modules
from core.models import TimeStampedModel
from tenants.models import User


class Category(TimeStampedModel):
    """
    Blog category for organizing articles.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Tag(TimeStampedModel):
    """
    Blog tag for categorizing articles.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Article(TimeStampedModel):
    """
    A blog article model with publishing workflow.
    """

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    # Basic fields
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(
        max_length=500, blank=True, help_text="Short summary of the article"
    )
    content = models.TextField()
    featured_image = models.URLField(
        blank=True, null=True, help_text="URL to featured image"
    )

    # Author and publishing
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    publish_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when article should be published",
    )

    # Organization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles")

    # Metadata
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-publish_date", "-created_at"]
        indexes = [
            models.Index(fields=["status"], name="article_status_idx"),
            models.Index(fields=["author"], name="article_author_idx"),
            models.Index(fields=["publish_date"], name="article_publish_date_idx"),
        ]

    def save(self, *args, **kwargs) -> None:
        # Auto-generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-set publish_date when status changes to published
        if self.status == "published" and not self.publish_date:
            self.publish_date = timezone.now()

        super().save(*args, **kwargs)

    def is_published(self) -> bool:
        """Check if article is published and publish date has passed."""
        if self.status != "published":
            return False
        if self.publish_date and self.publish_date > timezone.now():
            return False
        return True

    def __str__(self) -> str:
        return self.title
