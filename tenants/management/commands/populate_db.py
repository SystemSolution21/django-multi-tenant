import json
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from psycopg2 import connect, errors, sql
from tenant_users.tenants.tasks import provision_tenant
from tenant_users.tenants.utils import create_public_tenant

from tenants.models import User


class Command(BaseCommand):
    help = "Drops, recreates, and populates the database with tenants."

    def handle(self, *args: Any, **options: Any) -> None:
        self.drop_and_recreate_db()
        self.migrate_schemas()

        file_path = settings.BASE_DIR / "tenants" / "data" / "tenants.json"
        with open(file_path, "r") as f:
            self.tenants_data = json.load(f)

        self.create_public_tenant()
        self.create_private_tenants()

        self.stdout.write(self.style.SUCCESS("All tenants created successfully."))

    def drop_and_recreate_db(self) -> None:
        """
        Drops and recreates the database to ensure a clean state.
        Connects to 'postgres' database to perform these administrative actions.
        """
        self.stdout.write("Dropping and recreating the database...")

        db_settings = settings.DATABASES["default"]
        db_name = db_settings["NAME"]
        db_user = db_settings["USER"]
        db_password = db_settings["PASSWORD"]
        db_host = db_settings["HOST"]
        db_port = db_settings["PORT"]

        # Connect to 'postgres' system database
        conn = connect(
            dbname="postgres",
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Terminate existing connections to the target database
        try:
            cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()"
                ),
                [db_name],
            )
        except errors.InsufficientPrivilege:
            self.stdout.write(
                self.style.WARNING(
                    "Insufficient privileges to terminate connections. Proceeding..."
                )
            )

        # Drop and Create
        try:
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
            )
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
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
            self.style.SUCCESS(f"Database '{db_name}' recreated successfully.")
        )

    def migrate_schemas(self) -> None:
        """Runs the migrate_schemas command."""
        self.stdout.write("Running migrations...")
        call_command("migrate_schemas", "--shared", "--noinput")
        self.stdout.write(self.style.SUCCESS("Migrations completed."))

    def create_public_tenant(self) -> None:
        self.stdout.write("Creating the public tenant...")
        public_tenant_data = self.tenants_data[0]

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
        self.public_tenant = public_tenant
        self.root_user = root_user

        self.stdout.write(
            self.style.SUCCESS(
                f"Public tenant ('{public_tenant.schema_name}') has been successfully created."
            )
        )

    def create_private_tenants(self) -> None:
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
                self.style.SUCCESS(
                    f"Tenant '{tenant.schema_name}' has been successfully created."
                )
            )
