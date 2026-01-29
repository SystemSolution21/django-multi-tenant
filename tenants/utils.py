# tenants/utils.py

# Import standard libraries
from typing import Any, Tuple

# Import django libraries
from django.db import transaction
from django.http import HttpRequest
from django_tenants.utils import schema_context

# Import third-party libraries
from tenant_users.tenants.tasks import provision_tenant

# Import local modules
from tenants.models import Domain, Tenant, User


def create_tenant(tenant_data: dict[str, Any]) -> Tuple[Tenant, Domain]:
    """
    Create a new tenant with proper schema and domain setup.

    Args:
        tenant_data: Dictionary containing:
            - name: Tenant display name
            - schema_name: PostgreSQL schema name (lowercase, no spaces)
            - subdomain: Subdomain for routing
            - email: Owner's email
            - password: Owner's password (if creating new user)
            - root_user: Optional existing user to add as admin

    Returns:
        Tuple of (tenant, domain) objects
    """
    with transaction.atomic():
        # Create or get the tenant owner
        try:
            tenant_owner = User.objects.get(email=tenant_data["email"])
        except User.DoesNotExist:
            tenant_owner = User.objects.create(
                email=tenant_data["email"],
                password=tenant_data["password"],
                is_verified=True,
            )
            tenant_owner.save()

        # Create the tenant using django-tenant-users provision_tenant
        tenant, domain = provision_tenant(
            tenant_name=tenant_data["name"],
            tenant_slug=tenant_data["subdomain"],
            schema_name=tenant_data["schema_name"],
            owner=tenant_owner,
            is_superuser=True,
            is_staff=True,
        )

        # Add additional root user if specified and different from owner
        if (
            "root_user" in tenant_data
            and tenant_data["root_user"]
            and tenant_data["root_user"] != tenant_owner
        ):
            tenant.add_user(
                tenant_data["root_user"],
                is_superuser=True,
                is_staff=True,
            )

        return tenant, domain


def delete_tenant(tenant: Tenant) -> None:
    """
    Delete a tenant and its associated schema.
    WARNING: This will permanently delete all tenant data.
    """
    tenant.delete(force_drop=True)


def add_user_to_tenant(
    tenant: Tenant, user, is_superuser: bool = False, is_staff: bool = False
) -> None:
    """
    Add an existing user to a tenant with specified permissions.
    """
    tenant.add_user(
        user,
        is_superuser=is_superuser,
        is_staff=is_staff,
    )


def remove_user_from_tenant(tenant: Tenant, user) -> None:
    """
    Remove a user from a tenant.
    """
    tenant.remove_user(user)


def get_public_domain_url(request: HttpRequest) -> str | None:
    """
    Returns the full URL of the public domain, without a trailing slash.
    """
    public_domain_url = None
    try:
        with schema_context("public"):
            public_tenant = Tenant.objects.get(schema_name="public")
            # Try to find the primary domain first
            domain_obj = Domain.objects.filter(
                tenant=public_tenant, is_primary=True
            ).first()
            # Fallback to the first domain if no primary is set
            if not domain_obj:
                domain_obj = Domain.objects.filter(tenant=public_tenant).first()

            if domain_obj:
                domain = domain_obj.domain
                port = request.get_port()
                scheme = request.scheme
                # Avoid adding port if it's standard or already in the domain string
                if port and port not in ["80", "443"] and ":" not in domain:
                    domain = f"{domain}:{port}"
                public_domain_url = f"{scheme}://{domain}"
    except (Tenant.DoesNotExist, Domain.DoesNotExist):
        # Fails silently if public tenant or domain is not set up
        pass
    return public_domain_url
