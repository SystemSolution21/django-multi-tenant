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

- **`base.html`**: Features a smart Navbar(Sidebar) that changes links based on context (Public vs Tenant).
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

## Global Admin Workflow

The Public Schema (lvh.me) acts as the management layer.
It hosts the Landing Page, Sign Up Form, and the Global User Database.
Crucially, the **Tenant** table (the registry of all customers) lives only in the Public Schema.

### 1. Initial System Setup (Seeding)

To set up the environment from scratch (e.g., for development), the system uses a seeding script (often wrapped in a management command like `populate_db`):

1. **Database Reset**: Drop and recreate the application database to ensure a clean slate.
2. **Shared Migrations**: Run `migrate_schemas --shared` to create tables in the `public` schema.
3. **Public Tenant Creation**: Initialize the `public` tenant (domain: `lvh.me`).
4. **Demo Tenant Provisioning**: Iterate through a data file (e.g., `tenants.json`) to:
    - Create tenant owners (Users).
    - Call `provision_tenant` to create the schema and domain for each customer.
    - Link root admin users to new tenants for administrative access.

### 2. Ongoing Administration (Django Admin)

Global Superusers manage the system via the Admin Panel at `http://lvh.me:8000/admin/`.

- **Provisioning Tenants**: Standard "Add" buttons are disabled to prevent misconfiguration. Instead, use the custom **"Provision Tenant"** button on the Tenant List page. This ensures the User, Tenant, and Domain are created correctly in a single transaction.
- **User Management**: Users are global. Deleting a user from the Public Admin removes them from **all** tenants (`delete_user_globally`).
- **Impersonation**: Superusers can "Login as" any user to troubleshoot issues within specific tenant contexts.

## User Onboarding Workflow

- User visits lvh.me:8000/accounts/signup/ (Public Schema).
- User creates account: Added to tenants_user (Global) and linked to Public Tenant (so they can view the onboarding page).
- User fills Onboarding Form:
- App creates new Tenant (e.g., mycompany).
- App creates new Domain (mycompany.lvh.me).
- App switches context to mycompany schema -> Creates "First Project".
- Redirect: User is sent to mycompany.lvh.me:8000/ to start working.
