# core/context_processors.py

from django.http import HttpRequest
from django_tenants.utils import schema_context

from tenants.models import Domain, Tenant


def public_domain_context(request: HttpRequest) -> dict[str, str | None]:
    """
    Adds the full URL of the public domain to the template context.
    This allows creating absolute links to the main site from tenant sites.
    """
    public_domain_url = None
    try:
        # Switch to the public schema to query for the public tenant's domain
        with schema_context("public"):
            public_tenant = Tenant.objects.get(schema_name="public")
            primary_domain = Domain.objects.filter(
                tenant=public_tenant, is_primary=True
            ).first()
            if primary_domain:
                domain = primary_domain.domain
                port = request.get_port()
                if port and port not in ["80", "443"] and ":" not in domain:
                    domain = f"{domain}:{port}"
                public_domain_url = f"{request.scheme}://{domain}/"

    except Exception:
        # Fails silently if public tenant or domain is not set up
        pass
    return {"public_domain_url": public_domain_url}
