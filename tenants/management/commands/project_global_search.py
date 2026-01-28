# tenants/management/commands/project_global_search.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.core.management.base import BaseCommand
from django.db.models.manager import BaseManager
from django_tenants.utils import tenant_context

# Import local modules
from tenants.models import Tenant
from tasks.models import Project, Task
from blog.models import Article
from django.db.models import Q


class Command(BaseCommand):
    help = "Search for blog articles, projects and tasks across all tenant schemas and the public schema"

    def add_arguments(self, parser) -> None:
        parser.add_argument("query", type=str, help="The search keyword")

    def handle(self, *args, **options) -> None:
        query: dict[str, Any] = options["query"]
        self.stdout.write(msg=f"Global Search for: '{query}'")
        self.stdout.write(msg="-" * 40)

        results_found = False

        # 1. Get blog articles from public schema
        articles: BaseManager[Article] = Article.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )
        articles = articles.order_by("-created_at")
        if articles.exists():
            results_found = True
            self.stdout.write(msg=self.style.SUCCESS(text="\nBlog Articles:"))
            for art in articles:
                self.stdout.write(msg=f"[Title] - {art.title}")
                self.stdout.write(msg=f"[Content] - {art.content[:20]}")

        # 2. Get all tenants (subdomains / schemas)
        tenants: BaseManager[Tenant] = Tenant.objects.exclude(schema_name="public")
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
                            f"  [Task] - {t.name} (Project: {t.project.name})"
                        )

        if not results_found:
            self.stdout.write(self.style.WARNING("\nNo results found in any tenant."))
