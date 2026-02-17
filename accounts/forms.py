# accounts/forms.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify

# Import local modules
from django_tenants.utils import schema_context
from tenants.models import Tenant, User, UserInvitation


class CustomUserCreationForm(UserCreationForm):
    """
    A custom form for creating new users, using email as the username.
    """

    invitation_code = forms.CharField(
        required=False,
        help_text="Enter your invitation code if you have one.",
        label="Invitation Code (Optional)",
    )

    class Meta(UserCreationForm.Meta):  # type: ignore
        model = User
        fields = ("email", "first_name", "last_name")
        field_classes = {"email": UserCreationForm.Meta.field_classes["username"]}  # type: ignore

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.initial.get("invitation_code"):
            self.fields["invitation_code"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("invitation_code")
        email = cleaned_data.get("email")

        if code and email:
            # Validate the invitation code against the public schema
            with schema_context("public"):
                try:
                    invitation = UserInvitation.objects.get(
                        token=code, email=email, is_accepted=False
                    )
                    if invitation.is_expired:
                        self.add_error(
                            "invitation_code", "This invitation has expired."
                        )
                except UserInvitation.DoesNotExist:
                    self.add_error(
                        "invitation_code",
                        "Invalid invitation code or email mismatch. Please check your email.",
                    )
        return cleaned_data


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

    def clean_company_name(self):
        company_name = self.cleaned_data["company_name"]
        # Generate schema_name from company name (e.g., "My Company" -> "mycompany")
        schema_name = slugify(company_name).replace("-", "")

        # Validate characters
        if schema_name:
            validator = RegexValidator(
                regex=r"^[a-z0-9]+$",
                message="The company name generates an invalid subdomain. Only lowercase letters and numbers are allowed.",
            )
            validator(schema_name)

        # Check against reserved names
        reserved_names = getattr(settings, "TENANT_SUBDOMAIN_RESERVED_NAMES", [])
        if schema_name in reserved_names:
            raise ValidationError(
                f"The name '{company_name}' generates a reserved subdomain ('{schema_name}'). Please choose another."
            )

        # Check if tenant already exists
        if Tenant.objects.filter(schema_name=schema_name).exists():
            raise ValidationError(
                f"The workspace or company name '{company_name}' is already taken. Please choose another."
            )

        # Store schema_name in cleaned_data for the view to use
        self.cleaned_data["schema_name"] = schema_name

        return company_name
