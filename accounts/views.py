# accounts/views.py

# Import python libraries
from typing import Any, Callable, LiteralString, cast

# Import django libraries
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView

# Import local modules
from .forms import CustomUserCreationForm, OnboardingForm
from tenants.models import Tenant, User


class SignUpView(CreateView):
    """
    View for user registration/signup.
    """

    form_class = CustomUserCreationForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("onboarding")
    template_name = "registration/signup.html"

    def form_valid(self, form) -> HttpResponse:
        response: HttpResponse = super().form_valid(form=form)
        tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)
        user: User = cast(User, self.object)  # type: ignore[assignment]
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

        project_name: Any = form.cleaned_data["project_name"]

        # Generate a simple key from the name (e.g., "My Project" -> "MYP")
        # Ensure key is at least 2 chars, max 10
        key: LiteralString = "".join([c for c in project_name if c.isalnum()])[
            :3
        ].upper()
        if len(key) < 2:
            key = "PRJ"

        # Create the project
        Project.objects.create(
            name=project_name, key=key, description="Created during onboarding"
        )

        return super().form_valid(form=form)
