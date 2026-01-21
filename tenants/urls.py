# tenants/urls.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.urls import path

# Import local modules
from tenants.views import (
    AcceptInvitationView,
    TenantCreateView,
    TenantDeleteView,
    TenantDetailView,
    TenantListView,
    TenantUpdateView,
    TenantUserListView,
    UserInviteView,
)

# from . import views

urlpatterns: list[Any] = [
    path(route="", view=TenantListView.as_view(), name="tenant_list"),
    path(route="<int:pk>/", view=TenantDetailView.as_view(), name="tenant_detail"),
    path(route="create/", view=TenantCreateView.as_view(), name="tenant_create"),
    path(
        route="<int:pk>/update/", view=TenantUpdateView.as_view(), name="tenant_update"
    ),
    path(
        route="<int:pk>/delete/", view=TenantDeleteView.as_view(), name="tenant_delete"
    ),
    path(route="users/", view=TenantUserListView.as_view(), name="user_list"),
    path(route="users/invite/", view=UserInviteView.as_view(), name="user_invite"),
    path(
        route="invitations/<uuid:token>/accept/",
        view=AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
]
