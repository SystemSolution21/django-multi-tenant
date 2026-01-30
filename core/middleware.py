# core\middleware.py

# Import django libraries
from django.conf import settings
from django.db import connection

# Import third-party libraries
from tenant_users.tenants.middleware import TenantAccessMiddleware


class PublicTenantAccessMiddleware(TenantAccessMiddleware):
    """
    Custom middleware to allow authenticated users to access the public tenant
    without being members of it.
    """

    def process_request(self, request):
        # Check if the current schema is the public schema
        if connection.schema_name == settings.PUBLIC_SCHEMA_NAME:
            # Allow access to public schema for all users (authenticated or not).
            # This bypasses the strict membership check in TenantAccessMiddleware.
            return None

        # For other tenants, use the default behavior (enforce membership)
        return super().process_request(request)  # type: ignore[no-any-return]
