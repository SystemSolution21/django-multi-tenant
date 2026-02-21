# accounts/views.py

# Import standard libraries
from typing import Any, Callable, LiteralString, cast

# Import django libraries
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django_tenants.utils import schema_context

# Import third-party libraries
import structlog

# Import local modules
from .forms import CustomUserCreationForm, OnboardingForm
from tenants.models import Domain, Tenant, User, UserInvitation
from tenants.utils import create_tenant, get_public_domain_url

# Initialize logger
logger = structlog.get_logger()


class SignUpView(CreateView):
    """
    View for user account creation/signup.
    """

    form_class = CustomUserCreationForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("onboarding")
    template_name = "accounts/signup.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Redirect signups on tenant subdomains to the public domain.
        """
        if connection.schema_name != "public":
            public_url = get_public_domain_url(request)
            if public_url:
                return redirect(f"{public_url}{reverse_lazy('signup')}")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        invitation_code = self.request.GET.get("invitation_code")
        if invitation_code:
            initial["invitation_code"] = invitation_code
        return initial

    def form_valid(self, form) -> HttpResponse:
        with transaction.atomic():
            response: HttpResponse = super().form_valid(form=form)

            # 1. Add user to Public Tenant (Required for global login)
            public_tenant: Tenant = Tenant.objects.get(schema_name="public")
            user: User = cast(User, self.object)  # type: ignore[assignment]
            public_tenant.add_user(user_obj=user)

            # 2. Check for Invitation Code
            invitation_code = form.cleaned_data.get("invitation_code")
            if invitation_code:
                with schema_context("public"):
                    invitation = UserInvitation.objects.get(token=invitation_code)
                    target_tenant = invitation.tenant

                    # Add user to the target tenant
                    target_tenant.add_user(
                        user,
                        is_superuser=(invitation.role == "admin"),
                        is_staff=(invitation.role in ["admin", "staff"]),
                    )

                    # Update user role and invitation status
                    user.role = invitation.role
                    user.save()
                    invitation.is_accepted = True
                    invitation.save()

                    # Find the domain for the target tenant to redirect
                    domain_obj = Domain.objects.filter(
                        tenant=target_tenant, is_primary=True
                    ).first()
                    if not domain_obj:
                        domain_obj = Domain.objects.filter(tenant=target_tenant).first()

                    if domain_obj:
                        port = self.request.get_port()
                        domain = domain_obj.domain
                        if port and port not in ["80", "443"] and ":" not in domain:
                            domain = f"{domain}:{port}"

                        # Override the default success_url (onboarding) to go to the tenant
                        response = redirect(f"http://{domain}/")

            # Automatically log the user in after signup
            login(
                request=self.request,
                user=user,
                backend="tenant_users.permissions.backend.UserBackend",
            )
            logger.info(
                event="user_signed_up",
                user_id=user.pk,
                user_email=user.email,
            )
            return response


class OnboardingView(LoginRequiredMixin, FormView):
    """
    View to onboard a new user by asking for their first project.
    """

    template_name = "accounts/onboarding.html"
    form_class = OnboardingForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("index")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Restrict onboarding to the public schema.
        """
        if connection.schema_name != "public":
            return redirect("index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        # Import Project here to avoid issues if tasks app is not loaded in shared context
        from tasks.models import Project

        company_name: str = form.cleaned_data["company_name"]
        project_name: Any = form.cleaned_data["project_name"]

        user = cast(User, self.request.user)

        with transaction.atomic():
            # Generate schema_name from company name (e.g., "My Company" -> "mycompany")
            schema_name = form.cleaned_data.get("schema_name")
            if not schema_name:
                schema_name = f"tenant{user.pk}"

            # Create the Tenant
            tenant_data = {
                "name": company_name,
                "schema_name": schema_name,
                "subdomain": schema_name,
                "email": user.email,
                "password": "temp_password",  # User already exists, this is a placeholder
                "root_user": user,
            }
            create_tenant(tenant_data=tenant_data)

            # Refresh user to ensure we have the latest flags (like is_staff) set by create_tenant
            user.refresh_from_db()
            # Explicitly set the owner as Admin in our custom fields
            user.role = "admin"
            user.is_tenant_admin = True  # type: ignore
            user.save()

            # Generate a simple key from the name (e.g., "My Project" -> "MYP")
            key: LiteralString = "".join([c for c in project_name if c.isalnum()])[
                :4
            ].upper()
            if len(key) < 2:
                key = "PROJ"

            # Switch to the new tenant context to create the project
            with schema_context(schema_name):
                Project.objects.create(
                    name=project_name, key=key, description="Created during onboarding"
                )

        # Redirect to the new tenant's domain
        port = self.request.get_port()
        domain = f"{schema_name}.{settings.BASE_DOMAIN}"
        if port not in ["80", "443"]:
            domain = f"{domain}:{port}"

        logger.info(
            event="user_onboarded",
            user_id=user.pk,
            user_email=user.email,
            tenant_name=tenant_data["name"],
        )
        return redirect(f"http://{domain}/")
