# accounts/views.py

# Import python libraries
from typing import Any, Callable, cast

# Import django libraries
from django.db import connection
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Import local modules
from .forms import CustomUserCreationForm
from tenants.models import Tenant, User


class SignUpView(CreateView):
    """
    View for user registration/signup.
    """

    form_class = CustomUserCreationForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("login")
    template_name = "registration/signup.html"

    def form_valid(self, form) -> HttpResponse:
        response: HttpResponse = super().form_valid(form=form)
        tenant: Tenant = Tenant.objects.get(schema_name=connection.schema_name)
        user: User = cast(User, self.object)  # type: ignore[assignment]
        tenant.add_user(user_obj=user)
        return response
