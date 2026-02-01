# core/urls_public.py
"""
URLs for the public schema.
"""

# Import standard libraries
from typing import Any

# Import django libraries
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Import local modules
from blog.views import ArticleViewSet
from core.views import index_view
from tenants.api_views import GlobalSearchAPIView

# Register api viewsets routes
router = DefaultRouter()
router.register(prefix="blog", viewset=ArticleViewSet)

# Register URLs
urlpatterns: list[Any] = [
    path(route="", view=index_view, name="index"),
    path(route="api/", view=include(router.urls)),
    path(route="tenants/", view=include("tenants.urls")),
    path(route="admin/", view=admin.site.urls),
    path(route="accounts/", view=include("accounts.urls")),
    path(route="blog/", view=include("blog.urls")),
    path(
        route="api/global-search/",
        view=GlobalSearchAPIView.as_view(),
        name="global-search",
    ),
]
