from django.core.management.base import BaseCommand
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Force delete a tenant by schema name, dropping the schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "schema_name", type=str, help="The schema name of the tenant to delete"
        )

    def handle(self, *args, **options):
        schema_name = options["schema_name"]

        if schema_name == "public":
            self.stdout.write(self.style.ERROR("Cannot delete public tenant."))
            return

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
            self.stdout.write(f"Deleting tenant '{tenant.name}' ({schema_name})...")
            # delete(force_drop=True) drops the schema and deletes the record
            tenant.delete(force_drop=True)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted tenant '{schema_name}'.")
            )
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' does not exist.")
            )
