# TENANT AUDIT CHECKLIST (SaaS / django-tenants + django-tenant-users) ✅

> Purpose: A quick, repeatable checklist to verify the repository is properly configured for schema-per-tenant SaaS using `django-tenants` and `django-tenant-users`.

---

## Summary

- Project name: `django-multi-tenant`  
- Primary checks: Dependencies, settings, tenant models, middleware, routing, migrations, tenant lifecycle commands, tests, security, and operational docs.

---

## Repository & Dependencies ✅

- [ ] `django-tenants` present in `pyproject.toml` / lockfile (`django-tenants==x.y.z`)  
- [ ] `django-tenant-users` present in `pyproject.toml` / lockfile (`django-tenant-users==x.y.z`)  
- [ ] `psycopg2` or `psycopg2-binary` present for Postgres support

---

## Settings & Configuration ⚙️

- [ ] `DATABASES['default']['ENGINE']` set to `django_tenants.postgresql_backend`  
- [ ] `DATABASE_ROUTERS` includes `django_tenants.routers.TenantSyncRouter`  
- [ ] `SHARED_APPS` and `TENANT_APPS` are defined and separate in `core/settings.py`  
- [ ] `INSTALLED_APPS` is composed from `SHARED_APPS` + `TENANT_APPS` (no duplicates)  
- [ ] `TENANT_MODEL`, `TENANT_DOMAIN_MODEL` set (`"tenants.Tenant"`, `"tenants.Domain"`)  
- [ ] `PUBLIC_SCHEMA_NAME` and `PUBLIC_SCHEMA_URLCONF` configured  
- [ ] `AUTH_USER_MODEL` points to tenant user (e.g., `tenants.User`)  
- [ ] Auth backend(s) include `tenant_users` backend where required  
- [ ] `SESSION_COOKIE_DOMAIN` considered for subdomain session sharing (production)  
- [ ] `DEBUG`, `ALLOWED_HOSTS`, and secret management set for production readiness

---

## Middleware & Routing 🔐

- [ ] `django_tenants.middleware.main.TenantMainMiddleware` in `MIDDLEWARE`  
- [ ] `tenant_users` middleware / access middleware present (or intentionally extended)  
- [ ] Clear separation of `core/urls_public.py` (public) vs `core/urls.py` (tenant)  
- [ ] `SHOW_PUBLIC_IF_NO_TENANT_FOUND` behavior is deliberate and documented

---

## Models & Migrations 🧱

- [ ] `Tenant` model subclasses `TenantBase` (or `TenantMixin` per chosen lib)  
- [ ] `Domain` model subclasses `DomainMixin`  
- [ ] `User` extends `tenant_users` user (e.g., `UserProfile`/`UserBase`) and has tenant M2M where needed  
- [ ] Model migrations separate public/shared schema migrations and tenant migrations where applicable  
- [ ] Migration files reference `settings.AUTH_USER_MODEL` where appropriate

---

## Tenant Lifecycle & Management 🚀

- [ ] Existence of management commands for:
  - create/populate tenants (`provision_tenant`, `create_public_tenant`)  
  - schema migrations (`migrate_schemas --shared` usage)  
  - cleanup tasks (invitations, orphaned users)  
- [ ] Tenant creation flow ensures owner exists in public schema before provisioning tenant schema  
- [ ] Domain and primary domain assignment handled during provisioning

---

## Tenant-scoped Data & Apps 📦

- [ ] Tenant apps (e.g., `tasks`) listed in `TENANT_APPS` and not in `SHARED_APPS` unless intended  
- [ ] Shared apps (e.g., `blog`) in `SHARED_APPS` where data should be public/global  
- [ ] Any cross-schema access explicitly managed using `schema_context` or equivalent

---

## Authentication & Authorization 🔐

- [ ] Tenant membership checks enforced (via `tenant_users` middleware) for tenant routes  
- [ ] Public schema exceptions documented (e.g., onboarding, admin, invitation accept)  
- [ ] Invitation flow stores invitations in public schema if required and logic for acceptance migrates user into tenant properly

---

## Tests, QA & CI ✅

- [ ] Tests exist verifying:
  - tenant isolation (data not accessible across tenants)  
  - public schema behavior  
  - invitation & tenant-join flows  
- [ ] Unit/integration tests for `migrate_schemas`, `provision_tenant`, and `create_public_tenant` flows  
- [ ] CI runs migrations and tests in an environment with Postgres and `pg_trgm` extension if required

---

## Security & Production Considerations 🔒

- [ ] Ensure `SESSION_COOKIE_DOMAIN` and cookie security flags set for production  
- [ ] DB user has appropriate permissions (CREATE/DROP only for admin flows) — document required privileges  
- [ ] Backups and restore process covers tenant schemas (schema-aware backups)  
- [ ] Logging/monitoring set to capture tenant-level errors (include schema name in logs)

---

## Operational & Documentation 📚

- [ ] README contains tenant setup steps (create public tenant, migrate schemas, provision tenants)  
- [ ] Example `tenants.json` or scripts for local dev are present and documented  
- [ ] Admin/ops docs for running `populate_db` and `migrate_schemas` exist  
- [ ] Rollback plan for tenant schema deletion and data recovery documented

---

## Manual verification steps (quick) ▶️

1. Run migrations for shared apps:
   - `python manage.py migrate_schemas --shared --noinput`  
2. Create public tenant (if command exists):
   - Use `create_public_tenant` or `python manage.py populate_db` in dev environment  
3. Provision a test tenant:
   - Use `provision_tenant(...)` (management command or util) and confirm schema `tenant_schema_name.*` exists  
4. Create tenant data (create a `Project`/`Task`) in tenant schema and confirm not present in another tenant schema  
5. Test invitation flow (create invitation in public schema, accept, ensure user is added to tenant)  
6. Confirm tenant admin access and tenant user restrictions on tenant routes

---

## Notes / Callouts ⚠️

> - If `tenant_users` middleware has been intentionally replaced/extended, keep a short doc explaining why.  
> - Keep `DEBUG` and credentials out of committed files; verify environment variable usage for secrets.
