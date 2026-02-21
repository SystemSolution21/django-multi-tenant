# accounts/urls.py

# Import django libraries
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls.resolvers import URLPattern

# Import local modules
from .views import SignUpView, OnboardingView

urlpatterns: list[URLPattern] = [
    path(
        route="login/",
        view=auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(route="logout/", view=auth_views.LogoutView.as_view(), name="logout"),
    path(route="signup/", view=SignUpView.as_view(), name="signup"),
    path(route="onboarding/", view=OnboardingView.as_view(), name="onboarding"),
    path(
        route="password_reset/",
        view=auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
        ),
        name="password_reset",
    ),
    path(
        route="password_reset/done/",
        view=auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        route="reset/<uidb64>/<token>/",
        view=auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        route="reset/done/",
        view=auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
