# accounts/urls.py

# Import django libraries
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls.resolvers import URLPattern

# Import local modules
from .views import SignUpView

urlpatterns: list[URLPattern] = [
    path(
        route="login/",
        view=auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(route="logout/", view=auth_views.LogoutView.as_view(), name="logout"),
    path(route="signup/", view=SignUpView.as_view(), name="signup"),
]
