# tenants/management/commands/tenant_global_search.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.core.management.base import BaseCommand
from django.db.models.manager import BaseManager
from django_tenants.utils import tenant_context

# Import local modules
from tenants.models import Tenant
from tasks.models import Project, Task


class Command(BaseCommand):
    help = "Search for projects and tasks across ALL tenant schemas"

    def add_arguments(self, parser) -> None:
        parser.add_argument("query", type=str, help="The search keyword")

    def handle(self, *args, **options) -> None:
        query: dict[str, Any] = options["query"]
        self.stdout.write(msg=f"Global Search for: '{query}'")
        self.stdout.write(msg="-" * 40)

        # 1. Get all tenants (subdomains/schemas)
        tenants: BaseManager[Tenant] = Tenant.objects.exclude(schema_name="public")

        results_found = False

        # 2. Iterate through each tenant
        for tenant in tenants:
            # 3. Switches PostgreSQL 'search_path' to each tenant
            with tenant_context(tenant):
                # 4. ORM queries execute inside each specific tenant's schema
                # Get projects
                projects: BaseManager[Project] = Project.objects.filter(
                    name__icontains=query
                )
                # Get tasks
                tasks: BaseManager[Task] = Task.objects.filter(name__icontains=query)
                # 5. Check projects and tasks exist
                if projects.exists() or tasks.exists():
                    results_found = True
                    self.stdout.write(
                        msg=self.style.SUCCESS(
                            text=f"\nTenant: {tenant.name} ({tenant.schema_name})"
                        )
                    )

                    for p in projects:
                        self.stdout.write(f"  [Project] {p.name}")

                    for t in tasks:
                        self.stdout.write(
                            f"  [Task]    {t.name} (Project: {t.project.name})"
                        )

        if not results_found:
            self.stdout.write(self.style.WARNING("\nNo results found in any tenant."))
