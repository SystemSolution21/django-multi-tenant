# blog/urls.py
"""
URL patterns for the blog app web interface.
"""

# Import standard libraries
from typing import Any

# Import django libraries
from django.urls import path

# Import local modules
from blog.views import (
    ArticleCreateView,
    ArticleDeleteView,
    ArticleDetailView,
    ArticleListView,
    ArticleUpdateView,
    CategoryCreateView,
    TagCreateView,
)

# Blog URL patterns
urlpatterns: list[Any] = [
    path(route="", view=ArticleListView.as_view(), name="article_list"),
    path(route="<int:pk>/", view=ArticleDetailView.as_view(), name="article_detail"),
    path(route="create/", view=ArticleCreateView.as_view(), name="article_create"),
    path(
        route="<int:pk>/edit/", view=ArticleUpdateView.as_view(), name="article_update"
    ),
    path(
        route="<int:pk>/delete/",
        view=ArticleDeleteView.as_view(),
        name="article_delete",
    ),
    path(
        route="category/create/",
        view=CategoryCreateView.as_view(),
        name="category_create",
    ),
    path(route="tag/create/", view=TagCreateView.as_view(), name="tag_create"),
]
