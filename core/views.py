# core/views.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

# Import local modules
from blog.models import Article
from tasks.models import Project, Task


def index_view(request) -> JsonResponse | HttpResponse:
    """
    Index view for both public and tenant schemas.
    """
    # API request or Search request
    if request.path.startswith("/api/") or request.META.get(
        "HTTP_ACCEPT", ""
    ).startswith("application/json"):
        # Search Logic
        query = request.GET.get("q")
        if query:
            results = []
            if connection.schema_name == "public":
                articles = Article.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query)
                )[:5]
                for art in articles:
                    results.append(
                        {
                            "type": "Article",
                            "title": art.title,
                            "url": reverse("article_detail", args=[art.pk]),
                        }
                    )
            else:
                projects = Project.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )[:3]
                for proj in projects:
                    results.append(
                        {
                            "type": "Project",
                            "title": proj.name,
                            "url": reverse("project_detail", args=[proj.pk]),
                        }
                    )

                tasks = Task.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )[:5]
                for task in tasks:
                    results.append(
                        {
                            "type": "Task",
                            "title": task.name,
                            "url": reverse("task_detail", args=[task.pk]),
                        }
                    )

            return JsonResponse({"results": results})

        return JsonResponse(
            data={
                "name": "django-multi-tenant",
                "description": "A Django project with multi-tenancy support.",
                "version": "1.0.0",
                "schema": connection.schema_name,
            }
        )

    # Resume Onboarding Logic:
    # If a user is logged in on the public schema but belongs to no specific tenants
    # (only the public tenant), redirect them to onboarding.
    if (
        connection.schema_name == "public"
        and request.user.is_authenticated
        and not request.user.is_superuser
    ):
        if not request.user.tenants.exclude(schema_name="public").exists():  # type: ignore
            return redirect("onboarding")

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
