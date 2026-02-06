# tenants/admin.py

# Import standard libraries

# Import django libraries
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django_tenants.admin import TenantAdminMixin
from tenant_users.permissions.models import UserTenantPermissions

# Import local modules
from tenants.models import Domain, Tenant, User
from tenants.utils import delete_user_globally


class UserAdminForm(forms.ModelForm):
    is_staff = forms.BooleanField(
        label="Is staff",
        required=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_superuser = forms.BooleanField(
        label="Is superuser",
        required=False,
        help_text="Designates that this user has all permissions without explicitly assigning them.",
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["is_staff"].initial = self.instance.is_staff
            self.fields["is_superuser"].initial = self.instance.is_superuser

    def save(self, commit=True):
        # Save other user fields first
        user = super().save(commit=False)
        if commit:
            user.save()

        # The is_staff and is_superuser are properties; we cannot assign to them directly.
        # We must handle saving them based on the current schema context.
        is_staff = self.cleaned_data.get("is_staff", False)
        is_superuser = self.cleaned_data.get("is_superuser", False)

        if connection.schema_name == "public":
            # On public schema, update the global flags directly in the DB
            User.objects.filter(pk=user.pk).update(
                is_global_staff=is_staff, is_global_superuser=is_superuser
            )
        elif commit:
            # On a tenant schema, update the tenant-specific permissions
            utp, created = UserTenantPermissions.objects.get_or_create(profile=user)
            utp.is_staff = is_staff
            utp.is_superuser = is_superuser
            utp.save()

        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin class for the User model."""

    form = UserAdminForm

    list_display: list[str] = ["id", "email", "role", "is_active"]
    list_display_links: list[str] = ["id", "email"]
    search_fields: list[str] = ["email", "first_name", "last_name"]
    list_filter: list[str] = ["role", "is_active"]
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
                    "is_active",
                    "is_verified",
                    "is_staff",
                    "is_superuser",
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If we are in a tenant schema (not public), filter users to only those in this tenant
        if connection.schema_name != "public":
            return qs.filter(tenants__schema_name=connection.schema_name)
        return qs

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        # Prevent tenant admins from editing global superusers
        if (
            obj
            and obj.is_global_superuser
            and not getattr(request.user, "is_global_superuser", False)
        ):
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        # Prevent tenant admins from deleting global superusers
        if (
            obj
            and obj.is_global_superuser
            and not getattr(request.user, "is_global_superuser", False)
        ):
            return False
        return True

    def get_readonly_fields(self, request, obj=None) -> list[str]:
        if request.user.is_superuser:
            return []
        return ["is_staff", "is_superuser"]

    def delete_model(self, request, obj: User) -> None:
        delete_user_globally(obj)

    def delete_view(self, request, object_id, extra_context=None):
        # If we are on public schema, standard deletion analysis fails because
        # UserTenantPermissions table is missing.
        # We bypass the collector check and go straight to confirmation/deletion.
        if connection.schema_name == "public":
            obj = self.get_object(request, object_id)
            if obj is None:
                msg = f'{self.opts.verbose_name} with ID "{object_id}" doesn\'t exist. Perhaps it was deleted?'
                self.message_user(request, msg, messages.WARNING)
                url = reverse(
                    "admin:%s_%s_changelist"
                    % (self.opts.app_label, self.opts.model_name),
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(url)

            if request.method == "POST":
                self.delete_model(request, obj)
                self.message_user(
                    request, "User deleted successfully.", messages.SUCCESS
                )
                url = reverse(
                    "admin:%s_%s_changelist"
                    % (self.opts.app_label, self.opts.model_name),
                    current_app=self.admin_site.name,
                )
                return HttpResponseRedirect(url)

            # GET request - show simple confirmation
            context = {
                **self.admin_site.each_context(request),
                "object": obj,
                "opts": self.opts,
                "title": "Are you sure?",
                "deleted_objects": [
                    "User and all their permissions across tenants"
                ],  # Fake list
                "perms_lacking": [],
                "protected": [],
            }
            return render(request, "admin/delete_confirmation.html", context)

        return super().delete_view(request, object_id, extra_context)


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin class for the Tenant model."""

    list_display: list[str] = ["id", "name", "schema_name", "created_at"]
    list_display_links: list[str] = ["id", "name"]
    search_fields: list[str] = ["name", "schema_name"]

    def delete_model(self, request, obj) -> None:
        # Force delete the tenant, bypassing django-tenant-users safety checks
        obj.delete(force_drop=True)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display: list[str] = ["id", "domain", "tenant", "is_primary"]
    list_display_links: list[str] = ["id", "domain"]
    search_fields: list[str] = ["domain"]
