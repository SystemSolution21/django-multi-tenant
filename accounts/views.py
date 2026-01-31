# accounts/views.py

# Import standard libraries
from typing import Any, Callable, LiteralString, cast

# Import django libraries
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import CreateView, FormView
from django_tenants.utils import schema_context

# Import local modules
from .forms import CustomUserCreationForm, OnboardingForm
from tenants.models import Tenant, User
from tenants.utils import create_tenant


class SignUpView(CreateView):
    """
    View for user registration/signup.
    """

    form_class = CustomUserCreationForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("onboarding")
    template_name = "registration/signup.html"

    def form_valid(self, form) -> HttpResponse:
        with transaction.atomic():
            response: HttpResponse = super().form_valid(form=form)
            tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)
            user: User = cast(User, self.object)  # type: ignore[assignment]
            # This line is critical: it links the new user to the current (public) tenant
            tenant.add_user(user_obj=user)

            # Automatically log the user in after signup
            login(
                request=self.request,
                user=user,
                backend="tenant_users.permissions.backend.UserBackend",
            )
        return response


class OnboardingView(LoginRequiredMixin, FormView):
    """
    View to onboard a new user by asking for their first project.
    """

    template_name = "registration/onboarding.html"
    form_class = OnboardingForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("index")

    def form_valid(self, form) -> HttpResponse:
        # Import Project here to avoid issues if tasks app is not loaded in shared context
        from tasks.models import Project

        company_name: str = form.cleaned_data["company_name"]
        project_name: Any = form.cleaned_data["project_name"]

        # Generate schema_name from company name (e.g., "My Company" -> "mycompany")
        schema_name = slugify(company_name).replace("-", "")
        if not schema_name:
            schema_name = f"tenant{self.request.user.pk}"

        # Create the Tenant
        user = self.request.user
        tenant_data = {
            "name": company_name,
            "schema_name": schema_name,
            "subdomain": schema_name,
            "email": user.email,
            "password": "temp_password",  # User already exists, this is a placeholder
            "root_user": user,
        }
        create_tenant(tenant_data=tenant_data)

        # Generate a simple key from the name (e.g., "My Project" -> "MYP")
        key: LiteralString = "".join([c for c in project_name if c.isalnum()])[
            :3
        ].upper()
        if len(key) < 2:
            key = "PRJ"

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

        return redirect(f"http://{domain}/")
