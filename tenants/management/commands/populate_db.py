# tenants/management/commands/populate_db.py

# Import standard libraries
import json
from typing import Any

# Import django libraries
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# Import third-party libraries
from psycopg2 import connect, errors, sql
from psycopg2.extensions import connection, cursor
from tenant_users.tenants.tasks import provision_tenant

# Import local modules
from tenants.models import Domain, User, Tenant

TENANTS_JSON_PATH: str = settings.BASE_DIR / "tenants" / "data" / "tenants.json"


class Command(BaseCommand):
    """
    A management command to drop, recreate, and populate the database with tenants.
    """

    help = "Drops, recreates, and populates the database with tenants."

    def handle(self, *args: Any, **options: Any) -> None:
        """Handles the command execution."""
        self.drop_and_recreate_db()
        self.migrate_schemas()
        self.create_tenants()

        self.stdout.write(
            msg=self.style.SUCCESS(text="Database populated successfully.")
        )

    def drop_and_recreate_db(self) -> None:
        """
        Drops and recreates the database to ensure a clean state.
        Connects to 'postgres' database to perform these administrative actions.
        """

        self.stdout.write(msg="Dropping and recreating the database...")

        # Get database settings
        db_settings: dict[str, Any] = settings.DATABASES["default"]
        db_name: str = db_settings["NAME"]
        db_user: str = db_settings["USER"]
        db_password: str = db_settings["PASSWORD"]
        db_host: str = db_settings["HOST"]
        db_port: str = db_settings["PORT"]

        # Connect to 'postgres' system database
        conn: connection = connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.autocommit = True
        cur: cursor = conn.cursor()

        # Terminate existing connections to the target database
        try:
            cur.execute(
                query=sql.SQL(
                    string="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()"
                ),
                vars=[db_name],
            )
        except errors.InsufficientPrivilege:
            self.stdout.write(
                msg=self.style.WARNING(
                    text="Insufficient privileges to terminate connections. Proceeding..."
                )
            )

        # Drop and Create database
        try:
            cur.execute(
                query=sql.SQL(string="DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(db_name)
                )
            )
            cur.execute(
                query=sql.SQL(string="CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(db_name), sql.Identifier(db_user)
                )
            )
        except errors.InsufficientPrivilege:
            raise CommandError(
                f"Insufficient privileges to create the database.\n"
                f"Please grant CREATEDB to user '{db_user}'.\n"
                f"SQL command: ALTER USER {db_user} CREATEDB;"
            )

        cur.close()
        conn.close()
        self.stdout.write(
            msg=self.style.SUCCESS(text=f"Database '{db_name}' recreated successfully.")
        )

    def migrate_schemas(self) -> None:
        """Runs the migrate_schemas command."""

        self.stdout.write(msg="Running migrations...")

        # Migrate shared apps
        call_command("migrate_schemas", "--shared", "--noinput")
        self.stdout.write(msg=self.style.SUCCESS(text="Migrations completed."))

    def create_tenants(self) -> None:
        """Creates tenants from the JSON file."""
        self.stdout.write(msg="Creating tenants...")

        # Load tenant data from JSON file
        with open(file=TENANTS_JSON_PATH, mode="r", encoding="utf-8") as file:
            tenants_data: list[dict[str, Any]] = json.load(fp=file)

        # Create the public tenant (special case - creates tenant AND user)
        self.stdout.write(msg="Creating the public tenant...")
        public_tenant_data: dict[str, Any] = tenants_data[0]

        # Manually create the public tenant and superuser to avoid
        # calling `add_user` which tries to create a UserTenantPermissions
        # record in the public schema (where the table doesn't exist).
        with transaction.atomic():
            # Manually create the public tenant owner.
            # We cannot use create_superuser here because:
            # 1. It requires the public tenant to exist (circular dependency).
            # 2. It tries to add tenant permissions, which don't exist in the public schema.
            public_owner = User(
                email=public_tenant_data["owner"]["email"],
                is_active=True,
                is_verified=True,
                role="admin",
                is_global_superuser=True,
                is_global_staff=True,
            )
            public_owner.set_password(public_tenant_data["owner"]["password"])
            public_owner.save()

            # Create the public tenant instance
            public_tenant = Tenant.objects.create(
                schema_name=settings.PUBLIC_SCHEMA_NAME,
                name=public_tenant_data["name"],
                owner=public_owner,
                slug=public_tenant_data["subdomain"],
            )

            # Create the domain for the public tenant
            Domain.objects.create(
                domain=settings.BASE_DOMAIN, tenant=public_tenant, is_primary=True
            )

        # Create other tenants
        for tenant_data in tenants_data[1:]:
            self.stdout.write(msg=f"Creating tenant {tenant_data['name']}...")

            # Create the tenant owner user first (now public tenant exists)
            # Manual creation to avoid UserProfileManager.create_user trying to write to missing public permissions table
            tenant_owner = User(
                email=tenant_data["owner"]["email"],
                is_active=True,
                is_verified=True,
                role="admin",
            )
            tenant_owner.set_password(tenant_data["owner"]["password"])
            tenant_owner.save()

            # Create the tenant with the owner
            tenant, domain = provision_tenant(
                tenant_name=tenant_data["name"],
                tenant_slug=tenant_data["subdomain"],
                schema_name=tenant_data["schema_name"],
                owner=tenant_owner,
                is_superuser=True,
                is_staff=True,
            )

        self.stdout.write(
            msg=self.style.SUCCESS(text="All tenants created successfully.")
        )
