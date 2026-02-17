# tenants/urls.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.urls import path

# Import local modules
from tenants.views import (
    AcceptInvitationView,
    DeclineInvitationView,
    ResendInvitationView,
    DeleteInvitationView,
    TenantCreateView,
    TenantDeleteView,
    TenantDetailView,
    TenantListView,
    TenantUpdateView,
    TenantUserListView,
    UserEditView,
    UserInviteView,
    UserRemoveDeleteView,
    TenantTransferOwnershipView,
    PublicBlogSearchView,
    TenantSearchJSONView,
)

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
        route="users/invitations/<uuid:pk>/resend/",
        view=ResendInvitationView.as_view(),
        name="invitation_resend",
    ),
    path(
        route="users/invitations/<uuid:pk>/delete/",
        view=DeleteInvitationView.as_view(),
        name="invitation_delete",
    ),
    path(route="users/<int:pk>/edit/", view=UserEditView.as_view(), name="user_edit"),
    path(
        route="users/<int:pk>/remove/",
        view=UserRemoveDeleteView.as_view(),
        name="user_remove",
    ),
    path(
        route="users/<int:pk>/delete/",
        view=UserRemoveDeleteView.as_view(),
        name="user_delete",
    ),
    path(
        route="users/transfer-ownership/",
        view=TenantTransferOwnershipView.as_view(),
        name="tenant_transfer_ownership",
    ),
    path(
        route="invitations/<uuid:token>/accept/",
        view=AcceptInvitationView.as_view(),
        name="accept_invitation",
    ),
    path(
        route="invitations/<uuid:token>/decline/",
        view=DeclineInvitationView.as_view(),
        name="decline_invitation",
    ),
    path(
        route="search/",
        view=TenantSearchJSONView.as_view(),
        name="tenant_search_json",
    ),
    path(
        route="search/public/",
        view=PublicBlogSearchView.as_view(),
        name="public_blog_search",
    ),
]
