# core/views.py

# Import django libraries
from typing import Any
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from blog.models import Article

# Import local modules
from tasks.models import Project, Task


def index_view(request) -> JsonResponse | HttpResponse:
    """
    Index view for both public and tenant schemas.
    """
    # API request
    if request.path.startswith("/api/") or request.META.get(
        "HTTP_ACCEPT", ""
    ).startswith("application/json"):
        return JsonResponse(
            data={
                "name": "django-multi-tenant",
                "description": "A Django project with multi-tenancy support.",
                "version": "1.0.0",
                "schema": connection.schema_name,
            }
        )

    # HTML response for browser requests
    context: dict[str, Any] = {
        "schema_name": connection.schema_name,
        "is_public": connection.schema_name == "public",
    }

    # Add stats for tenant schemas
    if connection.schema_name != "public":
        context.update(
            {
                "project_count": Project.objects.count(),
                "task_count": Task.objects.count(),
                "completed_tasks": Task.objects.filter(is_done=True).count(),
            }
        )
    else:
        # Public schema stats
        context.update(
            {
                "article_count": Article.objects.count(),
            }
        )

    return render(request=request, template_name="core/index.html", context=context)
