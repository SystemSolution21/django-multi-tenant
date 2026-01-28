# core/context_processors.py

from typing import Any
from django.http import HttpRequest

from tenants.utils import get_public_domain_url


def public_domain_context(request: HttpRequest) -> dict[str, Any]:
    """
    Adds the public domain URL and a flag indicating if the current schema
    is public to the template context.
    """
    base_url = get_public_domain_url(request)
    # Add a trailing slash for use in templates like `href="{{ public_domain_url }}"`
    public_domain_url = f"{base_url}/" if base_url else None
    # Use getattr to safely access the tenant attribute added by middleware
    tenant = getattr(request, "tenant", None)
    is_public_schema = tenant.schema_name == "public" if tenant else False

    return {
        "public_domain_url": public_domain_url,
        "is_public_schema": is_public_schema,
    }
