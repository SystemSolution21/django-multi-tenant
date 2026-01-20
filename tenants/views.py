# tenants/views.py

# Import django libraries
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Import local modules
from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from tenants.utils import create_tenant

User = get_user_model()


class TenantListView(LoginRequiredMixin, ListView):
    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"


class TenantDetailView(LoginRequiredMixin, DetailView):
    model = Tenant
    template_name = "tenants/tenant_detail.html"


class TenantCreateView(LoginRequiredMixin, CreateView):
    model = Tenant
    fields = ["name", "schema_name"]
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenant_list")

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


class TenantUpdateView(LoginRequiredMixin, UpdateView):
    model = Tenant
    fields = ["name"]
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenant_list")


class TenantDeleteView(LoginRequiredMixin, DeleteView):
    model = Tenant
    template_name = "tenants/tenant_confirm_delete.html"
    success_url = reverse_lazy("tenant_list")


class TenantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tenant management.
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
