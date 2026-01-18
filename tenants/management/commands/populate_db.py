# tenants/management/commands/populate_db.py

# Import standard libraries
import json
from typing import Any

# Import django libraries
from django.core.management import BaseCommand, call_command
from psycopg2 import connect, sql

# Import local modules
from core import settings
from tenants.models import Domain, Tenant, User


class Command(BaseCommand):
    help = "Creates a public tenant and two demo tenants"
    tenants_data_file: str = "tenants/data/tenants.json"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(
            stdout=stdout, stderr=stderr, no_color=no_color, force_color=force_color
        )

        # Load the tenant data from JSON
        self.tenants_data: list[dict[str, Any]] = []
        with open(file=self.tenants_data_file, mode="r") as file:
            self.tenants_data = json.load(fp=file)

    def handle(self, *args, **kwargs) -> None:
        self.drop_and_recreate_db()

        call_command(command_name="migrate")
        self.create_tenants()

        self.stdout.write(
            msg=self.style.SUCCESS(
                text="Yay, database has been populated successfully."
            )
        )

    def drop_and_recreate_db(self) -> None:
        db: dict[str, Any] = settings.DATABASES["default"]
        db_name: str = db["NAME"]

        # Create a connection to the database
        conn = connect(
            dbname="postgres",
            user=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=db["PORT"],
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Terminate all connections to the database except the current one
        cur.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s
              AND pid <> pg_backend_pid();
            """,
            [db_name],
        )

        # Drop the database if it exists and create a new one
        cur.execute(
            sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
        )
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

        cur.close()
        conn.close()

    def create_tenants(self):
        for tenant_data in self.tenants_data:
            # Create the tenant
            tenant = Tenant(
                id=tenant_data["id"],
                name=tenant_data["name"],
                schema_name=tenant_data["schema_name"],
            )
            tenant.save()

            # Build the full domain name
            domain_str = settings.BASE_DOMAIN
            if tenant_data["subdomain"]:
                domain_str = f"{tenant_data['subdomain']}.{settings.BASE_DOMAIN}"

            # Create the domain
            domain = Domain(
                domain=domain_str,
                is_primary=tenant_data["schema_name"] == settings.PUBLIC_SCHEMA_NAME,
                tenant=tenant,
            )
            domain.save()

            # Create the tenant owner
            tenant_owner = User.objects.create_superuser(
                username=tenant_data["owner"]["username"],
                email=tenant_data["owner"]["email"],
                password=tenant_data["owner"]["password"],
            )
