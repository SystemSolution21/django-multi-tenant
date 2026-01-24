"""
Management command to clean up blog app migrations and database state.
Run with: python manage.py cleanup_blog
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Clean up blog app migrations and check database state'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("BLOG APP MIGRATION CLEANUP"))
        self.stdout.write("=" * 60)

        # Check migration records for blog app
        self.stdout.write("\n1. Checking migration records...")
        migrations = MigrationRecorder.Migration.objects.filter(app='blog')
        for migration in migrations:
            self.stdout.write(f"   - {migration.app}.{migration.name}")

        # Remove migration records for 0002 and 0003 if they exist
        self.stdout.write("\n2. Removing problematic migration records...")
        deleted_count = MigrationRecorder.Migration.objects.filter(
            app='blog',
            name__in=[
                '0002_category_tag_alter_article_options_article_author_and_more',
                '0003_remove_article_category_remove_article_tags_and_more'
            ]
        ).delete()
        self.stdout.write(self.style.SUCCESS(f"   Deleted {deleted_count[0]} migration records"))

        self.stdout.write("\n3. Checking blog_article table structure in each schema...")

        # Check public schema
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'blog_article'
                ORDER BY ordinal_position;
            """)
            public_columns = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f"\n   PUBLIC schema columns:")
            self.stdout.write(f"   {', '.join(public_columns)}")

        # Check each tenant schema
        extra_columns_found = False
        for tenant in Tenant.objects.exclude(schema_name='public'):
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = '{tenant.schema_name}' 
                    AND table_name = 'blog_article'
                    ORDER BY ordinal_position;
                """)
                tenant_columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"\n   {tenant.schema_name.upper()} schema columns:")
                self.stdout.write(f"   {', '.join(tenant_columns)}")
                
                # Check for extra columns
                expected_columns = ['id', 'created_at', 'updated_at', 'title', 'content']
                extra_columns = [col for col in tenant_columns if col not in expected_columns]
                if extra_columns:
                    extra_columns_found = True
                    self.stdout.write(self.style.WARNING(f"   ⚠ Extra columns found: {', '.join(extra_columns)}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("CLEANUP COMPLETE"))
        self.stdout.write("=" * 60)
        
        if extra_columns_found:
            self.stdout.write(self.style.WARNING("\n⚠ Extra columns detected in tenant schemas!"))
            self.stdout.write("\nTo remove extra columns, run:")
            self.stdout.write(self.style.SUCCESS("  python manage.py cleanup_blog --drop-columns"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ All schemas are clean!"))
            self.stdout.write("\nNext step: Run migrations")
            self.stdout.write("  python manage.py migrate")

    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-columns',
            action='store_true',
            help='Drop extra columns from tenant schemas',
        )

    def handle(self, *args, **options):
        if options['drop_columns']:
            self.drop_extra_columns()
        else:
            self.check_and_cleanup()

    def check_and_cleanup(self):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("BLOG APP MIGRATION CLEANUP"))
        self.stdout.write("=" * 60)

        # Check migration records
        self.stdout.write("\n1. Checking migration records...")
        migrations = MigrationRecorder.Migration.objects.filter(app='blog')
        for migration in migrations:
            self.stdout.write(f"   - {migration.app}.{migration.name}")

        # Remove problematic migration records
        self.stdout.write("\n2. Removing problematic migration records...")
        deleted_count = MigrationRecorder.Migration.objects.filter(
            app='blog',
            name__in=[
                '0002_category_tag_alter_article_options_article_author_and_more',
                '0003_remove_article_category_remove_article_tags_and_more'
            ]
        ).delete()
        self.stdout.write(self.style.SUCCESS(f"   Deleted {deleted_count[0]} migration records"))

        # Check table structures
        self.stdout.write("\n3. Checking blog_article table structure...")
        self.check_table_structures()

    def check_table_structures(self):
        # Check public schema
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'blog_article'
                ORDER BY ordinal_position;
            """)
            public_columns = [row[0] for row in cursor.fetchall()]
            self.stdout.write(f"\n   PUBLIC: {', '.join(public_columns)}")

        # Check tenant schemas
        extra_columns_found = False
        for tenant in Tenant.objects.exclude(schema_name='public'):
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = '{tenant.schema_name}' 
                    AND table_name = 'blog_article'
                    ORDER BY ordinal_position;
                """)
                tenant_columns = [row[0] for row in cursor.fetchall()]
                self.stdout.write(f"   {tenant.schema_name.upper()}: {', '.join(tenant_columns)}")
                
                expected = ['id', 'created_at', 'updated_at', 'title', 'content']
                extra = [col for col in tenant_columns if col not in expected]
                if extra:
                    extra_columns_found = True
                    self.stdout.write(self.style.WARNING(f"      ⚠ Extra: {', '.join(extra)}"))

        self.stdout.write("\n" + "=" * 60)
        if extra_columns_found:
            self.stdout.write(self.style.WARNING("⚠ Extra columns found!"))
            self.stdout.write("\nRun with --drop-columns to remove them:")
            self.stdout.write(self.style.SUCCESS("  python manage.py cleanup_blog --drop-columns"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ All clean!"))

    def drop_extra_columns(self):
        self.stdout.write(self.style.WARNING("\n⚠ DROPPING EXTRA COLUMNS FROM TENANT SCHEMAS"))
        
        columns_to_drop = [
            'author_id', 'excerpt', 'featured_image', 'publish_date',
            'slug', 'status', 'views_count', 'category_id'
        ]
        
        for tenant in Tenant.objects.exclude(schema_name='public'):
            self.stdout.write(f"\nProcessing {tenant.schema_name}...")
            
            with connection.cursor() as cursor:
                for column in columns_to_drop:
                    try:
                        cursor.execute(f"""
                            ALTER TABLE {tenant.schema_name}.blog_article 
                            DROP COLUMN IF EXISTS {column} CASCADE;
                        """)
                        self.stdout.write(f"  ✓ Dropped {column}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ Error dropping {column}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ Column cleanup complete!"))

