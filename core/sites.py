# core/sites.py

# Import django libraries
from django.contrib import admin
from django.http import HttpRequest


class TenantAdminSite(admin.AdminSite):
    site_header = "SaaS Administration"
    site_title = "SaaS Admin Portal"
    index_title = "Dashboard"

    def each_context(self, request: HttpRequest):
        context = super().each_context(request)

        tenant = getattr(request, "tenant", None)
        if tenant:
            context["site_header"] = f"{tenant.name} Administration"
            context["site_title"] = f"{tenant.name} Admin Portal"

        return context

    def get_app_list(self, request: HttpRequest, app_label: str | None = None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_list = super().get_app_list(request, app_label)  # type: ignore[call-arg]

        # For global superuser, show everything
        if getattr(request.user, "is_global_superuser", False):
            return app_list

        # For Tenant Admins (non-superusers), filter out restricted models
        new_app_list = []
        for app in app_list:
            # Hide the 'Tenants' app models (Tenant, Domain) but keep User if it's there
            if app["app_label"] == "tenants":
                allowed_models = [
                    m
                    for m in app["models"]
                    if m["object_name"] not in ["Tenant", "Domain", "DomainPart"]
                ]
                if allowed_models:
                    app["models"] = allowed_models
                    new_app_list.append(app)

            # Hide 'Auth' app (Groups) and 'Blog' (Shared app) entirely for tenant admins
            elif app["app_label"] in ["auth", "blog"]:
                continue

            else:
                new_app_list.append(app)

        return new_app_list
