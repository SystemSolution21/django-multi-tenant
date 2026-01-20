from django.urls import path

from . import views

urlpatterns = [
    path("", views.TenantListView.as_view(), name="tenant_list"),
    path("<int:pk>/", views.TenantDetailView.as_view(), name="tenant_detail"),
    path("create/", views.TenantCreateView.as_view(), name="tenant_create"),
    path("<int:pk>/update/", views.TenantUpdateView.as_view(), name="tenant_update"),
    path("<int:pk>/delete/", views.TenantDeleteView.as_view(), name="tenant_delete"),
]
