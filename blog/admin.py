# blog/admin.py

# Import django libraries
from django.contrib import admin

# Import local modules
from blog.models import Article
from core.admin import TimeStampedModelAdmin


class ArticleAdmin(TimeStampedModelAdmin):
    list_display: list[str] = ["id", "title", "created_at", "updated_at"]
    list_display_links: list[str] = ["id", "title"]
    search_fields: list[str] = ["title"]


admin.site.register(model_or_iterable=Article, admin_class=ArticleAdmin)
