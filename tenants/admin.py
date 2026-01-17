# tenants/admin.py

# Import django libraries
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

# Import local modules
from tenants.models import Domain, Tenant, User


class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin class for the Tenant model."""

    list_display = ["schema_name", "name", "created_at", "updated_at"]


class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display = ["domain", "tenant", "is_primary", "created_at", "updated_at"]


class UserAdmin(admin.ModelAdmin):
    """Admin class for the User model."""

    list_display = ["id", "email", "is_active"]
    list_display_links = ["id", "email"]
    search_fields = ["email"]
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
            "Administrative",
            {
                "fields": [
                    "tenants",
                    "last_login",
                    "is_active",
                    "is_verified",
                ],
            },
        ),
    ]


admin.site.register(model_or_iterable=Tenant, admin_class=TenantAdmin)
admin.site.register(model_or_iterable=Domain, admin_class=DomainAdmin)
admin.site.register(model_or_iterable=User, admin_class=UserAdmin)
