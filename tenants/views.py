# tenants/views.py

from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from tenants.models import Tenant
from tenants.utils import create_tenant


@login_required
def tenant_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        # In a real app, use a Django Form here
        tenant_data: dict[str, Any] = request.POST.dict()

        # 1. Create or Get the User (Owner)
        # Note: Users are global (public schema)
        # You might need logic here to check if user exists or create a new one

        # 2. Provision the Tenant
        # This handles Schema creation + Domain creation + Permission assignment

        # Inject the current user as the root user for the new tenant
        # create_tenant expects a User instance, not a string from POST
        tenant_data["root_user"] = request.user

        create_tenant(
            tenant_data,
        )

        return redirect("tenant_list")

    return render(request, "tenants/tenant_form.html")


@login_required
def tenant_list_view(request: HttpRequest) -> HttpResponse:
    # List all tenants
    tenants = Tenant.objects.all()
    return render(request, "tenants/tenant_list.html", {"tenants": tenants})
