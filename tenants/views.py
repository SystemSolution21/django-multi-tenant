# tenants/views.py

# Import django libraries
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse_lazy
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
from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from tenants.utils import create_tenant

User = get_user_model()


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
