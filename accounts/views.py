# accounts/views.py

# Import python libraries
from typing import Any, Callable

# Import django libraries
from django.urls import reverse_lazy
from django.views.generic import CreateView

# Import local modules
from .forms import CustomUserCreationForm


class SignUpView(CreateView):
    """
    View for user registration/signup.
    """

    form_class = CustomUserCreationForm
    success_url: str | Callable[..., Any] | None = reverse_lazy("login")
    template_name = "registration/signup.html"
