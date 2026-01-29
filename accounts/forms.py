# accounts/forms.py

# Import django libraries
from django.contrib.auth.forms import UserCreationForm

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
