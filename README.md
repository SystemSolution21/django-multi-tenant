# Building a Multi-tenant App with Django-tenants and django-tenant-users

This project is a SaaS multi-tenant application using the specific combination of:

- **Django** (core framework)
- **django-tenants** (schema-based multi-tenancy)
- **django-tenant-users** (shared user pool with per-tenant permissions)

## Project Overview

This project implements a **schema-based multi-tenancy** architecture, distinguishing between a "Public" context and a "Tenant" context.

### 1. Multi-Tenancy Architecture

- **Public Schema (`public`):**
  - Acts as the landing page and marketing site.
  - Used for global administration (managing tenants).
  - Renders the "SaaS Platform" brand and links to the Blog or Tenant list.
- **Tenant Schemas:**
  - Each customer (tenant) gets their own isolated schema (subdomain).
  - Contains the actual business data (Projects, Tasks, Users).
  - Displays a specific "Dashboard" with project/task counts.

### 2. The `tasks` Application

This is the core functional component of the SaaS platform, designed for tenants to manage their work.

- **Data Model:**
  - **Project:** A container for work with a unique key, name, and owner.
  - **Task:** A unit of work linked to a Project with status, priority, and assignee.
- **API Layer:**
  - Exposes a REST API using **Django Rest Framework (DRF)**.
  - `ProjectViewSet` and `TaskViewSet` handle CRUD operations.
  - Optimized with `.select_related` to prevent N+1 query issues.
- **UI Layer:**
  - Uses standard Django Server-Side Rendering (SSR) with Bootstrap 5.
  - Views enforce `TenantSchemaRequiredMixin` and `LoginRequiredMixin` for security.

### 3. User Interface

The templates are dynamic based on the tenant context:

- **`base.html`**: Features a smart Navbar that changes links based on context (Public vs Tenant).
- **`core/index.html`**:
  - **Public:** Displays a welcome message and blog links.
  - **Tenant:** Displays a Dashboard with statistics cards.

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
