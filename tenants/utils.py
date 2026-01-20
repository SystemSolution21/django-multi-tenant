# tenants/utils.py

# Import standard libraries
from typing import Any

# Import third-party libraries
from tenant_users.tenants.tasks import provision_tenant

# Import local modules
from tenants.models import User


def create_tenant(tenant_data: dict[str, Any]):
    # Create the tenant owner
    try:
        tenant_owner: User = User.objects.get(email=tenant_data["email"])
    except User.DoesNotExist:
        tenant_owner: User = User.objects.create_user(  # type: ignore
            email=tenant_data["email"],
            password=tenant_data["password"],
        )

    # Create the tenant
    tenant: Any = provision_tenant(
        tenant_name=tenant_data["name"],
        tenant_slug=tenant_data["subdomain"],
        schema_name=tenant_data["schema_name"],
        owner=tenant_owner,
        is_superuser=True,
        is_staff=True,
    )

    # Add the root user to the tenant
    tenant.add_user(
        tenant_data["root_user"],
        is_superuser=True,
        is_staff=True,
    )
