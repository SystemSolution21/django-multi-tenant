# core/urls_public.py
"""
URLs for the public schema.
"""

# Import standard libraries
from typing import Any

# Import django libraries
from django.conf import settings
from django.conf.urls.static import static as static_files
from django.contrib import admin
from django.urls import include, path
from django.templatetags.static import static
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

# Import local modules
from blog.views import ArticleViewSet
from core.views import index_view
from tenants.api_views import GlobalSearchAPIView

# Register api viewsets routes
router = DefaultRouter()
router.register(prefix="blog", viewset=ArticleViewSet)

# Register Public URLs
urlpatterns: list[Any] = [
    path(
        route="favicon.ico", view=RedirectView.as_view(url=static("favicon.ico"))
    ),  # favicon
    path(route="", view=index_view, name="index"),  # Home page
    path(route="api/", view=include(router.urls)),  # API routes
    path(route="tenants/", view=include("tenants.urls")),  # Tenants web UI
    path(route="admin/", view=admin.site.urls),  # Django admin
    path(route="accounts/", view=include("accounts.urls")),  # Auth URLs
    path(
        route="accounts/", view=include("django.contrib.auth.urls")
    ),  # Django Auth URLs (password reset, etc.)
    path(route="blog/", view=include("blog.urls")),  # Blog web UI
    path(
        route="api/global-search/",
        view=GlobalSearchAPIView.as_view(),
        name="global-search",
    ),  # Global search API
    path(route="hijack/", view=include("hijack.urls")),  # Hijack admin
]

# Serve media files in development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static_files(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
