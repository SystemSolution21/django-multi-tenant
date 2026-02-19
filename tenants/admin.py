# tenants/admin.py

# Import standard libraries
from typing import Any

# Import django libraries
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import connection
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils.html import format_html
from django_tenants.admin import TenantAdminMixin
from tenant_users.permissions.models import UserTenantPermissions

# Import local modules
from tenants.models import Domain, Tenant, User
from tenants.utils import create_tenant, delete_user_globally


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

    list_display: list[str] = [
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_global_superuser",
        "owned_tenants_count",
        "hijack_user_display",
    ]
    list_display_links: list[str] = ["email"]
    search_fields: list[str] = ["email", "first_name", "last_name"]
    list_filter: list[str] = ["role", "is_active", "is_global_superuser", "is_verified"]
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

    actions = ["delete_users_action"]

    def get_list_display(self, request):
        list_display: list[Any] = list(super().get_list_display(request))

        if not getattr(request.user, "is_global_superuser", False):
            # Only show hijack button to global superusers
            if "hijack_user_display" in list_display:
                list_display.remove("hijack_user_display")
        else:
            # Hide hijack button for the current user (self)
            def hijack_wrapper(obj):
                if obj.pk == request.user.pk:
                    return "-"
                return self.hijack_user_display(obj)

            hijack_wrapper.short_description = "Impersonate"

            if "hijack_user_display" in list_display:
                index = list_display.index("hijack_user_display")
                list_display[index] = hijack_wrapper

        return list_display

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If we are in a tenant schema (not public), filter users to only those in this tenant
        if connection.schema_name != "public":
            return qs.filter(tenants__schema_name=connection.schema_name)
        return qs

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        """
        Disable manual user creation in Admin.
        Users should be created via Signup or Invitation to ensure proper tenant association.
        """
        return False

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
        # Prevent deleting oneself
        if obj and obj == request.user:
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

    def owned_tenants_count(self, obj):
        return Tenant.objects.filter(owner=obj).count()

    owned_tenants_count.short_description = "Owned Tenants"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/hijack/",
                self.admin_site.admin_view(self.hijack_user_view),
                name="tenants_user_hijack",
            ),
        ]
        return custom_urls + urls

    def hijack_user_view(self, request, object_id):
        user = get_object_or_404(User, pk=object_id)
        if user == request.user:
            self.message_user(
                request, "You cannot impersonate yourself.", messages.WARNING
            )
            return HttpResponseRedirect(reverse("admin:tenants_user_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": f"Login as {user.email}",
            "user_obj": user,
            "hijack_url": reverse("hijack:acquire"),
        }
        return render(request, "tenants/admin/hijack_confirm.html", context)

    def hijack_user_display(self, obj):
        hijack_url = reverse("admin:tenants_user_hijack", args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="background-color: #f0ad4e; color: white; padding: 3px 10px; border-radius: 3px; text-decoration: none;">Login as</a>',
            hijack_url,
        )

    hijack_user_display.short_description = "Impersonate"

    @admin.action(description="Delete selected users")
    def delete_users_action(self, request, queryset):
        """
        Custom action to delete users safely, bypassing the standard collector
        which fails on public schema due to missing tenant tables.
        """
        if request.POST.get("post"):
            deleted_count = 0
            for user in queryset:
                if user == request.user:
                    self.message_user(
                        request, "You cannot delete yourself.", messages.ERROR
                    )
                    continue

                try:
                    delete_user_globally(user)
                    deleted_count += 1
                except ValidationError as e:
                    self.message_user(request, str(e), messages.ERROR)
                except Exception as e:
                    self.message_user(
                        request, f"Error deleting {user.email}: {e}", messages.ERROR
                    )

            if deleted_count > 0:
                self.message_user(
                    request,
                    f"Successfully deleted {deleted_count} users.",
                    messages.SUCCESS,
                )
            return None

        context = {
            **self.admin_site.each_context(request),
            "title": "Are you sure?",
            "deletable_objects": [f"{u.email}" for u in queryset],
            "queryset": queryset,
            "opts": self.opts,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "media": self.media,
        }
        return render(
            request, "admin/tenants/user/delete_selected_confirmation.html", context
        )


class ProvisionTenantForm(forms.Form):
    """Form for provisioning a new tenant (User+Tenant+Domain) from Admin."""

    name = forms.CharField(
        label="Tenant Name", max_length=100, help_text="Public display name"
    )
    subdomain = forms.CharField(
        label="Subdomain",
        max_length=63,
        help_text="Lowercase letters and numbers only. This will be the schema name.",
        validators=[
            RegexValidator(
                r"^[a-z0-9]+$", "Only lowercase letters and numbers are allowed."
            )
        ],
    )
    first_name = forms.CharField(label="Owner First Name", max_length=30)
    last_name = forms.CharField(label="Owner Last Name", max_length=30)
    email = forms.EmailField(label="Owner Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Owner Password")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_subdomain(self):
        subdomain = self.cleaned_data["subdomain"].lower()
        reserved_names = getattr(settings, "TENANT_SUBDOMAIN_RESERVED_NAMES", [])
        if subdomain in reserved_names:
            raise forms.ValidationError(f"'{subdomain}' is a reserved name.")
        if Tenant.objects.filter(schema_name=subdomain).exists():
            raise forms.ValidationError("A tenant with this subdomain already exists.")
        return subdomain


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin class for the Tenant model."""

    list_display: list[str] = [
        "name",
        "schema_name",
        "owner_display",
        "domains_display",
        "created_at",
    ]
    list_display_links: list[str] = ["name"]
    search_fields: list[str] = ["name", "schema_name", "owner__email"]
    list_filter = ["created_at"]

    def has_add_permission(self, request):
        """
        Disable manual tenant creation in Admin.
        Tenants should be created via Onboarding to ensure Domain and Owner setup.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.schema_name == "public":
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj) -> None:
        # Force delete the tenant, bypassing django-tenant-users safety checks
        obj.delete(force_drop=True)

    def owner_display(self, obj):
        if obj.owner:
            link = reverse("admin:tenants_user_change", args=[obj.owner.pk])
            return format_html('<a href="{}">{}</a>', link, obj.owner.email)
        return "-"

    owner_display.short_description = "Owner"

    def domains_display(self, obj):
        domain = Domain.objects.filter(tenant=obj, is_primary=True).first()
        if not domain:
            domain = Domain.objects.filter(tenant=obj).first()

        if domain:
            # Assuming port 8000 for development environment consistency
            url = f"http://{domain.domain}:8000"
            return format_html(
                '<a href="{}" target="_blank">{}</a> (<a href="{}/admin/" target="_blank">Admin</a>)',
                url,
                domain.domain,
                url,
            )
        return "No Domain"

    domains_display.short_description = "Domain / Admin"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "provision/",
                self.admin_site.admin_view(self.provision_view),
                name="tenants_tenant_provision",
            ),
        ]
        return custom_urls + urls

    def provision_view(self, request):
        if request.method == "POST":
            form = ProvisionTenantForm(request.POST)
            if form.is_valid():
                try:
                    tenant_data = {
                        "name": form.cleaned_data["name"],
                        "schema_name": form.cleaned_data["subdomain"],
                        "subdomain": form.cleaned_data["subdomain"],
                        "email": form.cleaned_data["email"],
                        "password": form.cleaned_data["password"],
                        "first_name": form.cleaned_data["first_name"],
                        "last_name": form.cleaned_data["last_name"],
                    }
                    tenant, domain = create_tenant(tenant_data)

                    self.message_user(
                        request,
                        f"Tenant '{tenant.name}' provisioned successfully.",
                        messages.SUCCESS,
                    )
                    return HttpResponseRedirect(
                        reverse("admin:tenants_tenant_changelist")
                    )
                except Exception as e:
                    self.message_user(
                        request, f"Error provisioning tenant: {e}", messages.ERROR
                    )
        else:
            form = ProvisionTenantForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Provision New Tenant",
        }
        return render(request, "admin/tenants/tenant/provision_form.html", context)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin class for the Domain model."""

    list_display: list[str] = ["id", "domain", "tenant", "is_primary"]
    list_display_links: list[str] = ["id", "domain"]
    search_fields: list[str] = ["domain"]
    list_filter = ["is_primary"]

    def has_add_permission(self, request):
        """
        Disable manual domain creation in Admin.
        Domains are provisioned automatically with Tenants.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.tenant.schema_name == "public":
            return False
        return super().has_delete_permission(request, obj)
