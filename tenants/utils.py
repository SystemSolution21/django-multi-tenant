# tenants/utils.py

# Import standard libraries
from typing import Any, cast
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
from django.db import connection, models, ProgrammingError
from django.db.models.fields.reverse_related import ManyToOneRel

# Import django libraries
from django.contrib.auth.models import UserManager
from django.db import transaction
from django.http import HttpRequest
from django.urls import reverse
from django_tenants.utils import schema_context

# Import third-party libraries
from tenant_users.tenants.tasks import provision_tenant
from tenant_users.permissions.models import UserTenantPermissions

# Import local modules
from tenants.models import Domain, Tenant, User, UserInvitation
from tasks.models import Project, Task


def create_tenant(tenant_data: dict[str, Any]):
    """
    Create a new tenant with proper schema and domain setup.

    Args:
        tenant_data: Dictionary containing:
            - name: Tenant display name
            - schema_name: PostgreSQL schema name (lowercase, no spaces)
            - subdomain: Subdomain for routing
            - email: Owner's email
            - password: Owner's password (if creating new user)
            - first_name: Owner's first name
            - last_name: Owner's last name
            - root_user: Optional existing user to add as admin

    Returns:
        Tuple of (tenant, domain) objects
    """
    with transaction.atomic():
        # Create or get the tenant owner
        try:
            tenant_owner = User.objects.get(email=tenant_data["email"])
        except User.DoesNotExist:
            tenant_owner = cast(UserManager, User.objects).create_user(
                username=tenant_data["email"],
                email=tenant_data["email"],
                password=tenant_data["password"],
                first_name=tenant_data.get("first_name", ""),
                last_name=tenant_data.get("last_name", ""),
            )
            tenant_owner.is_verified = True
            tenant_owner.save()

        # Create the tenant using django-tenant-users provision_tenant
        tenant, domain = provision_tenant(
            tenant_name=tenant_data["name"],
            tenant_slug=tenant_data["subdomain"],
            schema_name=tenant_data["schema_name"],
            owner=tenant_owner,
            is_superuser=True,
            is_staff=True,
        )

        # Add additional root user if specified and different from owner
        if (
            "root_user" in tenant_data
            and tenant_data["root_user"]
            and tenant_data["root_user"] != tenant_owner
        ):
            tenant.add_user(
                tenant_data["root_user"],
                is_superuser=True,
                is_staff=True,
            )

        return tenant, domain


def delete_tenant(tenant: Tenant) -> None:
    """
    Delete a tenant and its associated schema.
    WARNING: This will permanently delete all tenant data.
    """
    tenant.delete_tenant()


def add_user_to_tenant(
    tenant: Tenant, user, is_superuser: bool = False, is_staff: bool = False
) -> None:
    """
    Add an existing user to a tenant with specified permissions.
    """
    tenant.add_user(
        user,
        is_superuser=is_superuser,
        is_staff=is_staff,
    )


def remove_user_from_tenant(tenant: Tenant, user) -> None:
    """
    Remove a user from a tenant.
    """
    tenant.remove_user(user)


def get_public_domain_url(request: HttpRequest) -> str | None:
    """
    Returns the full URL of the public domain, without a trailing slash.
    """
    public_domain_url = None
    try:
        with schema_context("public"):
            public_tenant = Tenant.objects.get(schema_name="public")
            # Try to find the primary domain first
            domain_obj = Domain.objects.filter(
                tenant=public_tenant, is_primary=True
            ).first()
            # Fallback to the first domain if no primary is set
            if not domain_obj:
                domain_obj = Domain.objects.filter(tenant=public_tenant).first()

            if domain_obj:
                domain = domain_obj.domain
                port = request.get_port()
                scheme = request.scheme
                # Avoid adding port if it's standard or already in the domain string
                if port and port not in ["80", "443"] and ":" not in domain:
                    domain = f"{domain}:{port}"
                public_domain_url = f"{scheme}://{domain}"
    except (Tenant.DoesNotExist, Domain.DoesNotExist):
        # Fails silently if public tenant or domain is not set up
        pass
    return public_domain_url


def table_exists(table_name):
    """
    Check if a table exists in the current schema.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            sql="""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                AND table_name = %s
            )
            """,
            params=[table_name],
        )
        result: tuple[Any, ...] | None = cursor.fetchone()
        return result[0] if result else False


def delete_user_globally(user: User) -> None:
    """
    Safely delete a user from the system, cleaning up tenant references.
    """
    # Prevent deleting the owner of the public tenant
    with schema_context("public"):
        public_tenant = Tenant.objects.filter(schema_name="public").first()
        if public_tenant and public_tenant.owner == user:
            raise ValidationError(
                message=f"You cannot delete the owner of the {public_tenant.name}."
            )

    # Automatically delete any other tenants owned by this user
    for tenant in Tenant.objects.filter(owner=user):
        tenant.delete_tenant()

    # Before deleting the user, we must manually clean up any ForeignKeys
    # from tenant-specific models that point to this user.
    all_tenants = Tenant.objects.exclude(schema_name="public")
    for tenant in all_tenants:
        with schema_context(tenant.schema_name):
            try:
                # Nullify the 'owner' field for Projects and 'assignee' for Tasks
                if table_exists(table_name=Project._meta.db_table):
                    Project.objects.filter(owner=user).update(owner=None)
                if table_exists(table_name=Task._meta.db_table):
                    Task.objects.filter(assignee=user).update(assignee=None)
                # Delete UserTenantPermissions for this user to prevent integrity errors
                if table_exists(table_name=UserTenantPermissions._meta.db_table):
                    UserTenantPermissions.objects.filter(profile=user).delete()
            except ProgrammingError:
                pass

    # Temporarily disable on_delete behavior for tenant-specific models
    project_owner_field = cast(
        models.ForeignKey, Project._meta.get_field(field_name="owner")
    )
    task_assignee_field = cast(
        models.ForeignKey, Task._meta.get_field(field_name="assignee")
    )
    utp_profile_field = cast(
        models.ForeignKey, UserTenantPermissions._meta.get_field(field_name="profile")
    )

    # Cast remote_field to ManyToOneRel to satisfy type checker regarding on_delete
    project_owner_rel = cast(ManyToOneRel, project_owner_field.remote_field)
    task_assignee_rel = cast(ManyToOneRel, task_assignee_field.remote_field)
    utp_profile_rel = cast(ManyToOneRel, utp_profile_field.remote_field)

    original_project_on_delete = project_owner_rel.on_delete
    original_task_on_delete = task_assignee_rel.on_delete
    original_utp_on_delete = utp_profile_rel.on_delete

    try:
        # Tell the collector to do nothing for these relationships.
        project_owner_rel.on_delete = models.DO_NOTHING
        task_assignee_rel.on_delete = models.DO_NOTHING
        utp_profile_rel.on_delete = models.DO_NOTHING
        # This is the correct hard delete from Django, which will now succeed
        # because we have manually cleaned up cross-schema references.
        # We use filter().delete() to bypass django-tenant-users' safety check
        # which raises DeleteError on instance.delete().
        User.objects.filter(pk=user.pk).delete()
    finally:
        # Always restore the original on_delete behavior.
        project_owner_rel.on_delete = original_project_on_delete
        task_assignee_rel.on_delete = original_task_on_delete
        utp_profile_rel.on_delete = original_utp_on_delete


def send_invitation_email(request: HttpRequest, invitation: UserInvitation) -> None:
    """
    Sends the invitation email to the user.
    """
    # Use current tenant domain for invitation URL
    with schema_context("public"):
        tenant_domain: Domain | None = Domain.objects.filter(
            tenant=invitation.tenant, is_primary=True
        ).first()

    if tenant_domain:
        # Get the port from the current request
        port: str = request.get_port()
        domain_with_port: str = (
            f"{tenant_domain.domain}:{port}"
            if port not in ["80", "443"]
            else tenant_domain.domain
        )
        protocol = request.scheme
        invitation_url: str = f"{protocol}://{domain_with_port}/tenants/invitations/{invitation.token}/accept/"
    else:
        # Fallback to current domain if public domain not found
        invitation_url = request.build_absolute_uri(
            location=reverse(
                viewname="accept_invitation", kwargs={"token": invitation.token}
            )
        )

    send_mail(
        subject=f"Invitation to join {invitation.tenant.name}",
        message=f"You have been invited to join {invitation.tenant.name}. Click here to accept: {invitation_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        fail_silently=False,
    )
