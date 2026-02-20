# Tenant Management System

This project implements a multi-tenant architecture using `django-tenants` and `django-tenant-users`. It features a shared user pool (users exist globally) with isolated data schemas for each tenant.

## Prerequisites

The application requires a PostgreSQL database. The database user must have `CREATEDB` privileges to create new schemas dynamically.

See `database.txt` for the specific SQL commands to configure the database user and permissions.

## Configuration

Tenant definitions are stored in `tenants/data/tenants.json`.

### JSON Structure

1. **Public Tenant**: The first entry in the list. It manages the `public` schema, the base domain (e.g., `lvh.me`), and the global user table.
2. **Private Tenants**: Subsequent entries. Each creates an isolated schema and a subdomain.

**Example:**

```json
[
    {
        "name": "Public Tenant",
        "schema_name": "public",
        "subdomain": "", 
        "owner": { "email": "admin@lvh.me", "password": "..." }
    },
    {
        "name": "Demo Tenant",
        "schema_name": "demo",
        "subdomain": "demo",
        "owner": { "email": "admin@demo.lvh.me", "password": "..." }
    }
]
```

## Database Population

A custom management command is provided to bootstrap the environment.

```bash
python manage.py populate_db
```

**⚠️ Warning:** This command performs a **hard reset**. It drops the existing database, recreates it, runs migrations, and repopulates it with the data from `tenants.json`.

### Workflow

1. **Database Reset**: Connects to the `postgres` system database to drop and recreate the application database.
2. **Shared Migrations**: Runs `migrate_schemas --shared` to set up the public schema tables.
3. **Public Tenant**: Calls `create_public_tenant` to initialize the system.
4. **Private Tenants**: Iterates through the JSON data:
    * Creates the tenant owner (User).
    * Calls `provision_tenant` to create the schema and domain.
    * Links the root admin user to the new tenant for administrative access.

## Key Concepts

* **User Model**: Inherits from `UserProfile`. Users are global and live in the `public` schema. Authentication is shared, but authorization is per-tenant.
* **Tenant Model**: Inherits from `TenantBase`. Represents a customer and maps to a specific PostgreSQL schema.
* **Domain Model**: Inherits from `DomainMixin`. Routes incoming HTTP requests (e.g., `demo.lvh.me`) to the correct tenant schema.
* **Provisioning**: The `provision_tenant` utility handles the complex logic of creating the schema, setting up the domain, and assigning initial permissions to the owner.
