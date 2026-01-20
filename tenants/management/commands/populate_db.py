# tenants/management/commands/populate_db.py

# Import standard libraries
import json
from typing import Any

# Import django libraries
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

# Import third-party libraries
from psycopg2 import connect, errors, sql
from psycopg2.extensions import connection, cursor
from tenant_users.tenants.tasks import provision_tenant
from tenant_users.tenants.utils import create_public_tenant

# Import local modules
from tenants.models import User


class Command(BaseCommand):
    """
    A management command to drop, recreate, and populate the database with tenants.
    """

    help = "Drops, recreates, and populates the database with tenants."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handles the command.
        """
        # Drop and recreate the database
        self.drop_and_recreate_db()
        self.migrate_schemas()

        # Load tenant data
        file_path: str = settings.BASE_DIR / "tenants" / "data" / "tenants.json"
        with open(file=file_path, mode="r") as f:
            self.tenants_data: Any = json.load(fp=f)

        # Create the public tenant and private tenants
        self.create_public_tenant()
        self.create_private_tenants()

        self.stdout.write(
            msg=self.style.SUCCESS(text="All tenants created successfully.")
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

    def create_public_tenant(self) -> None:
        """
        Creates the public tenant.
        The public tenant is the first tenant in the list.
        """

        self.stdout.write(msg="Creating the public tenant...")

        # Get public tenant data
        public_tenant_data: dict[str, Any] = self.tenants_data[0]

        # Create the public tenant and the root user
        public_tenant: Any
        public_tenant, public_tenant_domain, root_user = create_public_tenant(
            domain_url=settings.BASE_DOMAIN,
            tenant_extra_data={"slug": public_tenant_data["subdomain"]},
            owner_email=public_tenant_data["owner"]["email"],
            is_superuser=True,
            is_staff=True,
            **{
                "password": public_tenant_data["owner"]["password"],
                "is_verified": True,
            },
        )
        self.public_tenant: Any = public_tenant
        self.root_user = root_user

        self.stdout.write(
            self.style.SUCCESS(
                f"Public tenant ('{public_tenant.schema_name}') has been successfully created."
            )
        )

    def create_private_tenants(self) -> None:
        """
        Creates the private tenants.
        The private tenants are the rest of the tenants in the list.
        """

        # Get private tenant data
        private_tenant_data = self.tenants_data[1:]

        for tenant_data in private_tenant_data:
            self.stdout.write(f"Creating tenant {tenant_data['schema_name']}...")

            # Create the tenant owner
            tenant_owner = User.objects.create_user(  # type: ignore
                email=tenant_data["owner"]["email"],
                password=tenant_data["owner"]["password"],
            )
            tenant_owner.is_verified = True
            tenant_owner.save()

            # Create the tenant
            tenant, domain = provision_tenant(
                tenant_name=tenant_data["name"],
                tenant_slug=tenant_data["subdomain"],
                schema_name=tenant_data["schema_name"],
                owner=tenant_owner,
                is_superuser=True,
                is_staff=True,
            )

            # Add the root user to the tenant
            tenant.add_user(
                self.root_user,
                is_superuser=True,
                is_staff=True,
            )

            self.stdout.write(
                msg=self.style.SUCCESS(
                    text=f"Tenant '{tenant.schema_name}' has been successfully created."
                )
            )
