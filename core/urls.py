# core/urls.py
"""
URLs for the tenant schemas.
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
from tasks.views import ProjectViewSet, TaskViewSet
from tenants.views import TenantViewSet

router = DefaultRouter()
router.register(prefix="blog", viewset=ArticleViewSet)
router.register(prefix="projects", viewset=ProjectViewSet)
router.register(prefix="tasks", viewset=TaskViewSet)
router.register(prefix="tenants", viewset=TenantViewSet)

urlpatterns: list[Any] = [
    path(route="", view=index_view, name="index"),
    path(route="api/", view=include(arg=router.urls)),
    path(route="tenants/", view=include(arg="tenants.urls")),
    path(route="admin/", view=admin.site.urls),
]
