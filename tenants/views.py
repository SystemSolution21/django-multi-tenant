# tenants/views.py

# Import standard libraries
from typing import TYPE_CHECKING, cast

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import connection
from django.db.models.manager import BaseManager
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

# Import third-party libraries
from django_tenants.utils import schema_context
from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated

# Import local modules
from tenants.mixins import TenantAdminRequiredMixin
from tenants.models import Tenant, User, UserInvitation
from tenants.serializers import TenantSerializer
from tenants.utils import create_tenant


class TenantListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List all tenants.
    """

    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"

    def test_func(self) -> bool:
        # Only allow access from public schema
        return connection.schema_name == "public" and self.request.user.is_superuser


class TenantDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Detail view for a tenant.
    """

    model = Tenant
    template_name = "tenants/tenant_detail.html"

    def test_func(self) -> bool:
        return self.request.user.is_superuser


class TenantCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Tenant
    fields: list[str] = ["name", "schema_name"]
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


class TenantUserListView(TenantAdminRequiredMixin, ListView):
    """List users within current tenant"""

    model = User
    template_name = "tenants/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.filter(tenants__schema_name=connection.schema_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_tenant = Tenant.objects.get(schema_name=connection.schema_name)
        # Query invitations from public schema (SHARED_APPS)
        with schema_context("public"):
            context["pending_invitations"] = UserInvitation.objects.filter(
                tenant=current_tenant, is_accepted=False
            ).order_by("-created_at")
        return context


class UserInviteView(TenantAdminRequiredMixin, CreateView):
    """Invite new user to tenant"""

    if TYPE_CHECKING:
        object: UserInvitation

    model = UserInvitation
    fields = ["email", "role"]
    template_name = "tenants/user_invite.html"
    success_url = reverse_lazy("user_list")

    def form_valid(self, form):
        user = cast(User, self.request.user)
        current_tenant = Tenant.objects.get(schema_name=connection.schema_name)

        form.instance.tenant = current_tenant
        form.instance.invited_by = user

        # Check if user already exists and is in tenant
        try:
            existing_user = User.objects.get(email=form.instance.email)
            if existing_user.tenants.filter(
                schema_name=connection.schema_name
            ).exists():
                messages.error(self.request, "User is already a member of this tenant.")
                return self.form_invalid(form)
        except User.DoesNotExist:
            pass

        # Check for existing invitations (from public schema)
        with schema_context("public"):
            # Check for pending invitations
            pending_invitation = UserInvitation.objects.filter(
                tenant=current_tenant, email=form.instance.email, is_accepted=False
            ).first()
            if pending_invitation:
                messages.error(
                    self.request,
                    f"An invitation has already been sent to {form.instance.email}.",
                )
                return self.form_invalid(form)

            # Delete any old accepted invitations to avoid unique constraint violation
            UserInvitation.objects.filter(
                tenant=current_tenant, email=form.instance.email, is_accepted=True
            ).delete()

        response = super().form_valid(form)

        # Send invitation email (self.object is now available)
        # Use public domain for invitation URL so user can login there
        from tenants.models import Domain

        with schema_context("public"):
            public_tenant = Tenant.objects.get(schema_name="public")
            public_domain = Domain.objects.filter(
                tenant=public_tenant, is_primary=True
            ).first()

        if public_domain:
            # Get the port from the current request
            port = self.request.get_port()
            domain_with_port = (
                f"{public_domain.domain}:{port}"
                if port not in ["80", "443"]
                else public_domain.domain
            )
            invitation_url = f"http://{domain_with_port}/tenants/invitations/{self.object.token}/accept/"
        else:
            # Fallback to current domain if public domain not found
            invitation_url = self.request.build_absolute_uri(
                reverse("accept_invitation", kwargs={"token": self.object.token})
            )

        send_mail(
            subject=f"Invitation to join {current_tenant.name}",
            message=f"You have been invited to join {current_tenant.name}. Click here to accept: {invitation_url}",
            from_email="noreply@yourapp.com",
            recipient_list=[self.object.email],
            fail_silently=False,
        )

        messages.success(self.request, f"Invitation sent to {self.object.email}")
        return response


class AcceptInvitationView(View):
    """Accept user invitation to join tenant"""

    def get(self, request, token):
        # Query invitation from public schema (SHARED_APPS)
        with schema_context("public"):
            invitation = get_object_or_404(
                UserInvitation, token=token, is_accepted=False
            )

        if invitation.is_expired:
            messages.error(request, "This invitation has expired.")
            return redirect("index")

        return render(
            request,
            "tenants/accept_invitation.html",
            {
                "invitation": invitation,
            },
        )

    def post(self, request, token):
        # Query invitation from public schema (SHARED_APPS)
        with schema_context("public"):
            invitation: UserInvitation = get_object_or_404(
                UserInvitation, token=token, is_accepted=False
            )

        if invitation.is_expired:
            messages.error(request, "This invitation has expired.")
            return redirect("index")

        if not request.user.is_authenticated:
            messages.error(request, "Please log in to accept the invitation.")
            return redirect("/admin/login/")

        if request.user.email != invitation.email:
            messages.error(request, "This invitation is for a different email address.")
            return redirect("index")

        # Add user to tenant
        invitation.tenant.add_user(
            request.user,
            is_superuser=(invitation.role == "admin"),
            is_staff=(invitation.role in ["admin", "staff"]),
        )

        # Update user role (users are in public schema)
        with schema_context("public"):
            user = User.objects.get(pk=request.user.pk)
            user.role = invitation.role
            if invitation.role == "admin":
                user.is_tenant_admin = True
            user.save()

            # Mark invitation as accepted (invitations are in public schema)
            invitation.is_accepted = True
            invitation.save()

        messages.success(request, f"Welcome to {invitation.tenant.name}!")

        # Redirect to tenant domain (query from public schema)
        try:
            from tenants.models import Domain

            with schema_context("public"):
                tenant_domain = Domain.objects.filter(
                    tenant=invitation.tenant, is_primary=True
                ).first()
            if tenant_domain:
                # Get the port from the current request
                port = request.get_port()
                domain_with_port = (
                    f"{tenant_domain.domain}:{port}"
                    if port not in ["80", "443"]
                    else tenant_domain.domain
                )
                return redirect(f"http://{domain_with_port}/tenants/users/")
        except Exception:
            pass

        return redirect("index")


class UserEditView(TenantAdminRequiredMixin, UpdateView):
    """Edit user within tenant"""

    model = User
    template_name = "tenants/user_edit.html"
    fields: list[str] = ["first_name", "last_name", "role", "is_tenant_admin"]

    def get_queryset(self) -> BaseManager[User]:
        # Only show users in current tenant
        return User.objects.filter(tenants=connection.tenant)

    def get_success_url(self) -> str:
        return reverse(viewname="user_list")


class UserRemoveView(LoginRequiredMixin, View):
    """
    Remove user from current tenant instead of deleting the user.
    """

    template_name = "tenants/user_confirm_remove.html"
    success_url = reverse_lazy("user_list")

    def get_object(self):
        """Get the user object from URL kwargs"""
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        """Show confirmation page"""
        user = self.get_object()
        return render(request, self.template_name, {"object": user})

    def post(self, request, *args, **kwargs):
        """Remove user from current tenant instead of deleting the user."""
        user = cast(User, self.get_object())
        tenant = Tenant.objects.get(schema_name=connection.schema_name)

        # Remove user from tenant (keeps user account intact)
        tenant.remove_user(user_obj=user)

        # Delete any invitations for this user in this tenant (from public schema)
        with schema_context("public"):
            UserInvitation.objects.filter(tenant=tenant, email=user.email).delete()

        messages.success(
            request, f"User {user.email} has been removed from {tenant.name}"
        )

        return HttpResponseRedirect(self.success_url)
