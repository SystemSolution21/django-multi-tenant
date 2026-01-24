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

router = DefaultRouter()
router.register(prefix="blog", viewset=ArticleViewSet)

urlpatterns: list[Any] = [
    path(route="", view=index_view, name="index"),
    path(route="api/", view=include(arg=router.urls)),
    path(route="tenants/", view=include(arg="tenants.urls")),
    path(route="admin/", view=admin.site.urls),
    path(route="blog/", view=include(arg="blog.urls")),
]
