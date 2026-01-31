# accounts/forms.py

# Import django libraries
from django.contrib.auth.forms import UserCreationForm
from django import forms

# Import local modules
from tenants.models import User


class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating new users, using email as the username.
    """

    class Meta(UserCreationForm.Meta):  # type: ignore
        model = User
        fields = ("email", "first_name", "last_name")
        field_classes = {"email": UserCreationForm.Meta.field_classes["username"]}  # type: ignore


class OnboardingForm(forms.Form):
    """
    Form for the onboarding step to create the first project.
    """

    company_name = forms.CharField(
        max_length=100,
        label="Workspace Name",
        help_text="Enter the name of your company or workspace.",
    )
    project_name = forms.CharField(
        max_length=100,
        label="Project Name",
        help_text="Enter the name of your first project.",
    )
