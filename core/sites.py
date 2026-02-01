from django.contrib import admin
from django.http import HttpRequest


class TenantAdminSite(admin.AdminSite):
    site_header = "SaaS Administration"
    site_title = "SaaS Admin Portal"
    index_title = "Dashboard"

    def get_app_list(self, request: HttpRequest):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_list = super().get_app_list(request)

        # If superuser, show everything
        if request.user.is_superuser:
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

            # Hide 'Auth' app (Groups) entirely for tenant admins
            elif app["app_label"] == "auth":
                continue

            else:
                new_app_list.append(app)

        return new_app_list
