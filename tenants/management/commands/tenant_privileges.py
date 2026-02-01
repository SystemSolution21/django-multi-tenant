from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tenants.models import Tenant
from tenant_users.permissions.models import UserTenantPermissions
from django_tenants.utils import schema_context

User = get_user_model()
user = User.objects.get(email="testuser@example.com")

# 1. Remove Superuser status (Critical for isolation)
user.is_superuser = False
user.is_staff = True  # Required to access /admin/
user.save()

tenant = Tenant.objects.get(schema_name="testusercompany")

# 2. Assign specific permissions for the Tasks app INSIDE the tenant context
with schema_context(tenant.schema_name):
    # Get content types for your models
    project_ct = ContentType.objects.get(app_label="tasks", model="project")
    task_ct = ContentType.objects.get(app_label="tasks", model="task")

    # Get permissions
    permissions = Permission.objects.filter(content_type__in=[project_ct, task_ct])

    utp = UserTenantPermissions.objects.get(profile=user)
    utp.user_permissions.set(permissions)

print(f"Permissions updated for {user.email}")
print(f"User is staff: {user.is_staff}")
print(f"User is superuser: {user.is_superuser}")
