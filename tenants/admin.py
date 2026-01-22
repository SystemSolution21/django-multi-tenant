# tenants/admin.py

# Import django libraries
from django.contrib import admin

# Import local modules
from tenants.models import Domain, Tenant, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin class for the User model."""

    list_display = ["id", "email", "role", "is_tenant_admin", "is_active"]
    list_display_links = ["id", "email"]
    search_fields = ["email", "first_name", "last_name"]
    list_filter = ["role", "is_tenant_admin", "is_active"]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "email",
                    "password",
                ],
            },
        ),
        (
            "Personal Info",
            {
                "fields": [
                    "first_name",
                    "last_name",
                    "phone",
                ],
            },
        ),
        (
            "Permissions",
            {
                "fields": [
                    "role",
                    "is_tenant_admin",
                    "is_active",
                    "is_verified",
                ],
            },
        ),
        (
            "Important dates",
            {
                "fields": [
                    "last_login",
                ],
            },
        ),
    ]


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin class for the Tenant model."""

    list_display = ["id", "name", "schema_name", "created_at"]
    list_display_links = ["id", "name"]
    search_fields = ["name", "schema_name"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display = ["id", "domain", "tenant", "is_primary"]
    list_display_links = ["id", "domain"]
    search_fields = ["domain"]
