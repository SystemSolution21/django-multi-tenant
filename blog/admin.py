# blog/admin.py

# Import django libraries
from django.contrib import admin

# Import local modules
from blog.models import Article, Category, Tag
from core.admin import TimeStampedModelAdmin


@admin.register(Category)
class CategoryAdmin(TimeStampedModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(TimeStampedModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(TimeStampedModelAdmin):
    list_display: list[str] = [
        "id",
        "title",
        "status",
        "author",
        "publish_date",
        "views_count",
    ]
    list_display_links: list[str] = ["id", "title"]
    search_fields: list[str] = ["title", "content"]
    list_filter = ["status", "category", "publish_date"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["author", "category", "tags"]
