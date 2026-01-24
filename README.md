# Building a Multi-tenant App with Django-tenants and django-tenant-users

This project is a SaaS multi-tenant application using the specific combination of:

- **Django** (core framework)
- **django-tenants** (schema-based multi-tenancy)
- **django-tenant-users** (shared user pool with per-tenant permissions)

## Prerequisites

The application requires a PostgreSQL database. The database user must have `CREATEDB` privileges to create new schemas dynamically.

See `database.txt` for the specific SQL commands to configure the database user and permissions.

## User Management

- Users are **global** (live in `public` schema)
- Authentication is shared across all tenants
- Authorization (permissions) is per-tenant

## Schema Context

- The `public` schema is the global (shared) namespace
- Each tenant has its own PostgreSQL schema (e.g., `demo1`, `demo2`)
- The `connection.schema_name` variable indicates the current schema context

## Workflow

1. **Database Reset**: Connect to the `postgres` system database to drop and recreate the application database.
2. **Shared Migrations**: Run `migrate_schemas --shared` to set up the public schema tables.
3. **Public Tenant**: Call `create_public_tenant` to initialize the system.
4. **Private Tenants**: Iterate through the JSON data:
    - Create the tenant owner (User)
    - Call `provision_tenant` to create the schema and domain
    - Link the root admin user to the new tenant for administrative access
