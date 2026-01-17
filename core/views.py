# core/views.py

# Import django libraries
from django.http import JsonResponse


def index_view(request) -> JsonResponse:
    """
    Index view for the tenant schemas.
    """
    return JsonResponse(
        data={
            "name": "django-multi-tenant",
            "description": "A Django project with multi-tenancy support.",
            "version": "1.0.0",
        }
    )
