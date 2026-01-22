# SaaS multi-tenant application Explanation

This project is a SaaS multi-tenant application using the specific combination of:

- **Django** (core framework)
- **django-tenants** (schema-based multi-tenancy)
- **django-tenant-users** (shared user pool with per-tenant permissions)

Key architectural considerations I'll remember:

## User Management

- Users are **global** (live in `public` schema)
- Users can belong to **multiple tenants**
- Use `tenant.add_user()` / `tenant.remove_user()` instead of standard Django user operations
- Avoid `UserProfile.objects.delete()` - use `UserProfile.objects.delete_user()` if actually deleting

## Schema Context

- Always check `connection.schema_name` for tenant vs public context
- Use `request.tenant` or `Tenant.objects.get(schema_name=connection.schema_name)`
- Different permissions/views for public vs tenant schemas

## Database Operations

- Tenant data is isolated in separate PostgreSQL schemas
- Auth/contenttypes must stay in same database
- Use `TenantSyncRouter` for proper routing

## Permissions

- Custom `role` field instead of standard Django `is_staff`/`is_superuser`
- Per-tenant permissions via django-tenant-users
- Global superusers vs tenant admins
