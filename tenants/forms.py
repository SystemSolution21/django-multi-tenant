# tenants/forms.py

# Import standard libraries
from typing import Any

# Import django libraries
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Import local modules
from tenants.models import Tenant, UserInvitation


class TenantForm(forms.ModelForm):
    """
    Form for creating tenants with validation for schema_name containing only
    lowercase letters and numbers and not in reserved names.
    """

    class Meta:
        model = Tenant
        fields: list[str] = ["name", "schema_name"]
        help_texts: dict[str, str] = {
            "schema_name": "This will be your subdomain (e.g., company.lvh.me). Lowercase letters and numbers only.",
        }

    def clean_schema_name(self) -> Any:
        schema_name: Any = self.cleaned_data["schema_name"].lower()

        # Validate characters
        validator = RegexValidator(
            regex=r"^[a-z0-9]+$",
            message="Only lowercase letters and numbers are allowed.",
        )
        validator(value=schema_name)

        # Check against reserved names
        reserved_names: list[str] = getattr(
            settings, "TENANT_SUBDOMAIN_RESERVED_NAMES", []
        )
        if schema_name in reserved_names:
            raise ValidationError(
                message=f"The name '{schema_name}' is reserved and cannot be used."
            )

        return schema_name


class UserInvitationForm(forms.ModelForm):
    """
    Form for inviting users to a tenant.
    """

    class Meta:
        model = UserInvitation
        fields = ["email", "role"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "colleague@example.com"}),
        }
        help_texts = {
            "email": "Enter the email address of the person you want to invite. If they are not yet a registered user, they will be invited to sign up.",
        }
