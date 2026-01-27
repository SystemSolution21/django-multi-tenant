# tenants/api_views.py

# Import standard libraries
import concurrent.futures
from concurrent.futures import Future
from typing import Any

# Import django libraries
from django.db.models.manager import BaseManager
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_tenants.utils import tenant_context

# Import local modules
from tenants.models import Tenant
from tasks.models import Project, Task


def search_in_tenant_for_api(tenant, query) -> list[Any]:
    """
    Performs a search within a single tenant's schema and returns structured data.
    This function is designed to be run in a parallel thread.
    """

    with tenant_context(tenant):
        # Get projects and tasks
        projects: BaseManager[Project] = Project.objects.filter(name__icontains=query)
        tasks: BaseManager[Task] = Task.objects.filter(name__icontains=query)

        # Initialize results list
        results: list[dict[str, Any]] = []

        # Get the tenant's domain
        base_url: str = f"http://{tenant.domains.first().domain}"

        # Add projects to results
        for p in projects:
            results.append(
                {
                    "tenant_name": tenant.name,
                    "type": "Project",
                    "name": p.name,
                    "url": f"{base_url}/projects/{p.pk}/",
                }
            )

        # Add tasks to results
        for t in tasks:
            results.append(
                {
                    "tenant_name": tenant.name,
                    "type": "Task",
                    "name": t.name,
                    "url": f"{base_url}/tasks/{t.pk}/",
                }
            )
    return results


class GlobalSearchAPIView(APIView):
    """
    An API endpoint for superusers to perform a search across all tenants.
    Usage: GET /api/global-search/?q=<query>
    """

    def get(self, request, *args, **kwargs) -> Response:
        # 1. User Authentication
        if not request.user.is_superuser:
            return Response(
                data={
                    "error": "Forbidden: You do not have permission to perform this action."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        query: Any = request.query_params.get("q", None)
        if not query or len(query) < 2:
            return Response(
                data={
                    "error": "A search query parameter 'q' with at least 2 characters is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Get all tenants (subdomains/schemas)
        tenants: BaseManager[Tenant] = Tenant.objects.exclude(schema_name="public")
        all_results: list[dict[str, Any]] = []

        # 2. Concurrent Execution: Use a thread pool to search tenants in parallel.
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_tenant: dict[Future[list[Any]], Tenant] = {
                executor.submit(search_in_tenant_for_api, tenant, query): tenant
                for tenant in tenants
            }

            for future in concurrent.futures.as_completed(future_to_tenant):
                try:
                    tenant_results: list[Any] = future.result()
                    if tenant_results:
                        all_results.extend(tenant_results)
                except Exception as exc:
                    # In a production app, you should log this error.
                    print(
                        f"Tenant search for {future_to_tenant[future].schema_name} generated an exception: {exc}"
                    )

        return Response({"results": all_results}, status=status.HTTP_200_OK)
