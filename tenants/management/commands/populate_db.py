import json
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import (
    get_tenant_domain_model,
    get_tenant_model,
    schema_context,
)
from psycopg2 import connect, errors, sql


class Command(BaseCommand):
    help = "Drops, recreates, and populates the database with tenants."

    def handle(self, *args: Any, **options: Any) -> None:
        self.drop_and_recreate_db()
        self.migrate_schemas()
        self.create_tenants()

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
        call_command("migrate_schemas", interactive=False)
        self.stdout.write(self.style.SUCCESS("Migrations completed."))

    def create_tenants(self) -> None:
        """Reads tenants.json and creates tenants, domains, and users."""
        self.stdout.write("Creating tenants...")

        Tenant = get_tenant_model()
        Domain = get_tenant_domain_model()
        User = get_user_model()

        file_path = settings.BASE_DIR / "tenants" / "data" / "tenants.json"
        with open(file_path, "r") as f:
            tenants_data = json.load(f)

        for data in tenants_data:
            # Create Tenant
            tenant: Any = Tenant.objects.create(
                schema_name=data["schema_name"], name=data["name"]
            )

            # Create Domain
            domain_name = (
                f"{data['subdomain']}.{settings.BASE_DOMAIN}"
                if data["subdomain"]
                else settings.BASE_DOMAIN
            )
            Domain.objects.create(domain=domain_name, tenant=tenant, is_primary=True)

            # Create Superuser inside the tenant's schema
            with schema_context(tenant.schema_name):
                User.objects.create_superuser(
                    username=data["owner"]["username"],
                    email=data["owner"]["email"],
                    password=data["owner"]["password"],
                )

            self.stdout.write(f"Created tenant: {data['name']} ({domain_name})")

        self.stdout.write(self.style.SUCCESS("All tenants created successfully."))
