# tenants/views.py

# Import standard libraries
from typing import TYPE_CHECKING, Any, Literal, cast

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import connection
from django.db.models import Q
from django.db.models.manager import BaseManager
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
from tenants.models import Domain, Tenant, User, UserInvitation
from tenants.serializers import TenantSerializer
from tenants.utils import create_tenant
from blog.models import Article
from tasks.models import Project, Task


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
    """
    Create a new tenant.
    """

    model = Tenant
    fields: list[str] = ["name", "schema_name"]
    template_name = "tenants/tenant_form.html"
    success_url: Any = reverse_lazy("tenant_list")

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def form_valid(self, form) -> HttpResponseRedirect:
        user = self.request.user
        assert isinstance(user, User), "User must be authenticated"

        tenant_data: dict[str, Any] = {
            "name": form.cleaned_data["name"],
            "schema_name": form.cleaned_data["schema_name"],
            "subdomain": form.cleaned_data["schema_name"],
            "email": user.email,
            "password": "temp_password",
            "root_user": user,
        }
        create_tenant(tenant_data=tenant_data)
        return redirect(to="tenant_list")


class TenantUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing tenant.
    """

    model = Tenant
    fields: list[str] = ["name"]
    template_name = "tenants/tenant_form.html"
    success_url: Any = reverse_lazy("tenant_list")

    def test_func(self) -> bool:
        return self.request.user.is_superuser


class TenantDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete a tenant.
    """

    model = Tenant
    template_name = "tenants/tenant_confirm_delete.html"
    success_url: Any = reverse_lazy("tenant_list")

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def form_valid(self, form) -> HttpResponseRedirect:
        success_url: str = self.get_success_url()
        self.object.delete(force_drop=True)
        return HttpResponseRedirect(redirect_to=success_url)


class TenantSelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Allow tenant admin to update their own tenant details only"""

    model = Tenant
    fields: list[str] = ["name"]  # Not schema_name!
    template_name = "tenants/tenant_self_update.html"

    def test_func(self) -> Any | Literal[False]:
        # Only tenant admin can edit their own tenant
        return self.request.user.is_staff and connection.schema_name != "public"

    def get_object(self) -> Tenant:
        # Get current tenant from schema context
        return Tenant.objects.get(schema_name=connection.schema_name)


class IsPublicSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers from the public schema.
    """

    def has_permission(self, request, view) -> Any | Any:
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
    permission_classes: list[Any] = [IsAuthenticated, IsPublicSuperUser]


class TenantUserListView(TenantAdminRequiredMixin, ListView):
    """List users within current tenant"""

    model = User
    template_name = "tenants/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.filter(tenants__schema_name=connection.schema_name)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        current_tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)
        # Query invitations from public schema
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
    fields: list[str] = ["email", "role"]
    template_name = "tenants/user_invite.html"
    success_url: Any = reverse_lazy("user_list")

    def form_valid(self, form) -> HttpResponse:
        user: User = cast(User, self.request.user)
        current_tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)

        form.instance.tenant = current_tenant
        form.instance.invited_by = user

        # Check if user already exists and is in tenant
        try:
            existing_user: User = User.objects.get(email=form.instance.email)
            if existing_user.tenants.filter(
                schema_name=connection.schema_name
            ).exists():
                messages.error(
                    request=self.request,
                    message="User is already a member of this tenant.",
                )
                return self.form_invalid(form=form)
        except User.DoesNotExist:
            pass

        # Check for existing invitations (from public schema)
        with schema_context("public"):
            # Check for pending invitations
            pending_invitation: UserInvitation | None = UserInvitation.objects.filter(
                tenant=current_tenant, email=form.instance.email, is_accepted=False
            ).first()
            if pending_invitation:
                if pending_invitation.is_expired:
                    # Automatically clean up expired invitation so we can send a new one
                    pending_invitation.delete()
                else:
                    messages.error(
                        request=self.request,
                        message=f"An invitation has already been sent to {form.instance.email}.",
                    )
                    return self.form_invalid(form=form)

            # Delete any old accepted invitations to avoid unique constraint violation
            UserInvitation.objects.filter(
                tenant=current_tenant, email=form.instance.email, is_accepted=True
            ).delete()

        response: HttpResponse = super().form_valid(form=form)

        # Send invitation email (self.object is now available)
        # Use current tenant domain for invitation URL

        with schema_context("public"):
            tenant_domain: Domain | None = Domain.objects.filter(
                tenant=current_tenant, is_primary=True
            ).first()

        if tenant_domain:
            # Get the port from the current request
            port: str = self.request.get_port()
            domain_with_port: str = (
                f"{tenant_domain.domain}:{port}"
                if port not in ["80", "443"]
                else tenant_domain.domain
            )
            invitation_url: str = f"http://{domain_with_port}/tenants/invitations/{self.object.token}/accept/"
        else:
            # Fallback to current domain if public domain not found
            invitation_url = self.request.build_absolute_uri(
                location=reverse(
                    viewname="accept_invitation", kwargs={"token": self.object.token}
                )
            )

        send_mail(
            subject=f"Invitation to join {current_tenant.name}",
            message=f"You have been invited to join {current_tenant.name}. Click here to accept: {invitation_url}",
            from_email="noreply@yourapp.com",
            recipient_list=[self.object.email],
            fail_silently=False,
        )

        messages.success(
            request=self.request, message=f"Invitation sent to {self.object.email}"
        )
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

        # UX Improvement: Warn immediately if logged in as the wrong user
        if request.user.is_authenticated and request.user.email != invitation.email:
            messages.warning(
                request,
                f"You are logged in as {request.user.email}. This invitation is for {invitation.email}. Please log out and log in as the correct user.",
            )

        return render(
            request,
            "tenants/accept_invitation.html",
            {
                "invitation": invitation,
            },
        )

    def post(self, request, token):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to accept the invitation.")
            return redirect(f"{reverse('login')}?next={request.path}")

        # Perform all operations in public schema context
        with schema_context("public"):
            invitation: UserInvitation = get_object_or_404(
                UserInvitation, token=token, is_accepted=False
            )

            if invitation.is_expired:
                messages.error(request, "This invitation has expired.")
                return redirect("index")

            if request.user.email != invitation.email:
                messages.error(
                    request,
                    f"You are logged in as {request.user.email}. This invitation is for {invitation.email}. Please log out and try again.",
                )
                return redirect("index")

            # Add user to tenant
            invitation.tenant.add_user(
                request.user,
                is_superuser=(invitation.role == "admin"),
                is_staff=(invitation.role in ["admin", "staff"]),
            )

            # Update user role
            user = User.objects.get(pk=request.user.pk)
            user.role = invitation.role
            user.save()

            # Mark invitation as accepted
            invitation.is_accepted = True
            invitation.save()

            # Get tenant domain for redirect
            tenant_domain = Domain.objects.filter(
                tenant=invitation.tenant, is_primary=True
            ).first()

        messages.success(request, f"Welcome to {invitation.tenant.name}!")

        if tenant_domain:
            port = request.get_port()
            domain_with_port = (
                f"{tenant_domain.domain}:{port}"
                if port not in ["80", "443"]
                else tenant_domain.domain
            )
            return redirect(f"http://{domain_with_port}/tenants/users/")

        return redirect("index")


class DeclineInvitationView(View):
    """Decline user invitation"""

    def get(self, request, token) -> HttpResponse:
        # Query invitation from public schema
        with schema_context("public"):
            invitation: UserInvitation = get_object_or_404(
                klass=UserInvitation, token=token, is_accepted=False
            )

        return render(
            request=request,
            template_name="tenants/decline_invitation.html",
            context={
                "invitation": invitation,
            },
        )

    def post(self, request, token) -> HttpResponseRedirect:
        with schema_context("public"):
            invitation: UserInvitation = get_object_or_404(
                klass=UserInvitation, token=token, is_accepted=False
            )
            invitation.delete()

        messages.success(request=request, message="Invitation declined successfully.")
        return redirect(to="index")


class UserEditView(TenantAdminRequiredMixin, UpdateView):
    """Edit user within tenant"""

    model = User
    template_name = "tenants/user_edit.html"
    fields: list[str] = ["first_name", "last_name", "role"]

    def get_queryset(self) -> BaseManager[User]:
        # Only show users in current tenant
        return User.objects.filter(tenants=connection.tenant)

    def get_success_url(self) -> str:
        return reverse(viewname="user_list")


class UserRemoveView(TenantAdminRequiredMixin, View):
    """
    Remove user from current tenant instead of deleting the user.
    """

    template_name: str = "tenants/user_confirm_remove.html"
    success_url: Any = reverse_lazy("user_list")

    def get_object(self) -> User:
        """Get the user object from URL kwargs"""
        return get_object_or_404(klass=User, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """Show confirmation page"""
        user: User = self.get_object()
        return render(
            request=request, template_name=self.template_name, context={"object": user}
        )

    def post(self, request, *args, **kwargs) -> HttpResponseRedirect:
        """Remove user from current tenant instead of deleting the user."""
        user: User = cast(User, self.get_object())
        tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)

        # Remove user from tenant (keeps user account intact)
        tenant.remove_user(user_obj=user)

        # Delete any invitations for this user in this tenant (from public schema)
        with schema_context("public"):
            UserInvitation.objects.filter(tenant=tenant, email=user.email).delete()

        messages.success(
            request=request,
            message=f"User {user.email} has been removed from {tenant.name}",
        )

        return HttpResponseRedirect(redirect_to=self.success_url)


class TenantSearchJSONView(LoginRequiredMixin, View):
    """
    Search for local tenant content (Projects, Tasks) and return JSON.
    """

    def get(self, request: Any) -> JsonResponse:
        query: Any = request.GET.get("q", "")
        results: list[dict[str, Any]] = []

        # This search is only for tenant schemas
        if query and len(query) >= 2 and connection.schema_name != "public":
            # Search Projects
            # _default_manager bypass any custom 'objects' manager that might be filtering results
            projects = Project._default_manager.filter(name__icontains=query)[:5]
            for project in projects:
                results.append(
                    {
                        "title": project.name,
                        "url": reverse(
                            viewname="project_detail", kwargs={"pk": project.pk}
                        ),
                        "type": "Project",
                    }
                )

            # Search Tasks
            tasks = Task._default_manager.filter(name__icontains=query)[:5]
            for task in tasks:
                results.append(
                    {
                        "title": task.name,
                        "url": reverse(viewname="task_detail", kwargs={"pk": task.pk}),
                        "type": "Task",
                    }
                )

        return JsonResponse(data={"results": results})


class PublicBlogSearchView(View):
    """
    Search for blog articles in the public schema.
    """

    def get(self, request) -> JsonResponse:
        query: Any = request.GET.get("q", "")
        results: list[dict[str, Any]] = []

        if query and len(query) >= 2:
            with schema_context("public"):
                # Search title OR content and get distinct results
                articles = Article.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query)
                ).distinct()[:5]

                for article in articles:
                    # Blog articles are in the public schema, so the URL should be relative.
                    url: str = f"/blog/{article.pk}/"

                    results.append(
                        {"title": article.title, "url": url, "type": "Article"}
                    )
        return JsonResponse(data={"results": results})
