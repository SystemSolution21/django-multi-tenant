# tenants/views.py

# Import standard libraries
from typing import cast

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated

# Import local modules
from tenants.models import Tenant, User, UserInvitation
from tenants.serializers import TenantSerializer
from tenants.utils import create_tenant


class TenantListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"

    def test_func(self):
        # Only allow access from public schema
        return connection.schema_name == "public" and self.request.user.is_superuser


class TenantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Tenant
    template_name = "tenants/tenant_detail.html"

    def test_func(self):
        return self.request.user.is_superuser


class TenantCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Tenant
    fields = ["name", "schema_name"]
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenant_list")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        user = self.request.user
        assert isinstance(user, User), "User must be authenticated"

        tenant_data = {
            "name": form.cleaned_data["name"],
            "schema_name": form.cleaned_data["schema_name"],
            "subdomain": form.cleaned_data["schema_name"],
            "email": user.email,
            "password": "temp_password",
            "root_user": user,
        }
        create_tenant(tenant_data)
        return redirect("tenant_list")


class TenantUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tenant
    fields = ["name"]
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenant_list")

    def test_func(self):
        return self.request.user.is_superuser


class TenantDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tenant
    template_name = "tenants/tenant_confirm_delete.html"
    success_url = reverse_lazy("tenant_list")

    def test_func(self):
        return self.request.user.is_superuser


class TenantSelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Allow tenant admin to update their own tenant details only"""

    model = Tenant
    fields = ["name"]  # Not schema_name!
    template_name = "tenants/tenant_self_update.html"

    def test_func(self):
        # Only tenant admin can edit their own tenant
        return self.request.user.is_staff and connection.schema_name != "public"

    def get_object(self):
        # Get current tenant from schema context
        return Tenant.objects.get(schema_name=connection.schema_name)


class IsPublicSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers from the public schema.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_superuser
            and connection.schema_name == "public"
        )


class TenantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tenant management.
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsPublicSuperUser]


class TenantUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List users within current tenant"""

    model = User
    template_name = "tenants/user_list.html"
    context_object_name = "users"

    def test_func(self):
        user = cast(User, self.request.user)
        return user.is_tenant_admin or user.role == "admin"

    def get_queryset(self):
        # Only show users from current tenant
        return User.objects.filter(tenants__schema_name=connection.schema_name)


class UserInviteView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Invite new user to tenant"""

    model = UserInvitation
    fields = ["email", "role"]
    template_name = "tenants/user_invite.html"
    success_url = reverse_lazy("user_list")

    def test_func(self):
        user = cast(User, self.request.user)
        return user.is_tenant_admin or user.role == "admin"

    def form_valid(self, form):
        user = cast(User, self.request.user)
        form.instance.tenant = user.tenants.get(schema_name=connection.schema_name)
        form.instance.invited_by = self.request.user

        # Send invitation email
        invitation_url = self.request.build_absolute_uri(
            reverse("accept_invitation", kwargs={"token": form.instance.token})
        )

        send_mail(
            subject=f"Invitation to join {form.instance.tenant.name}",
            message=f"You have been invited to join {form.instance.tenant.name}. Click here to accept: {invitation_url}",
            from_email="noreply@yourapp.com",
            recipient_list=[form.instance.email],
            fail_silently=False,
        )

        messages.success(self.request, f"Invitation sent to {form.instance.email}")
        return super().form_valid(form)
