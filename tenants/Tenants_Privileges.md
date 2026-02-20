# The `admin@demo.lvh.me` should have **tenant-scoped admin privileges** - full control within their tenant but no access to other tenants or global system management

## Privileges for `admin@demo.lvh.me`

### ✅ **SHOULD HAVE ACCESS TO:**

**Within Demo Tenant Schema:**

- **User Management**: Invite/edit/delete users within demo tenant (but not other tenants)
- **Tasks App**: Full CRUD on projects and tasks in demo schema
- **Django Admin**: Access to `/admin/` for demo-specific models
- **API Endpoints**: Full access to `/api/tasks/`, `/api/projects/` in demo context
- **Tenant Settings**: Modify demo tenant name, preferences (but not schema_name) (but not other tenants)

### ❌ **SHOULD NOT HAVE ACCESS TO:**

**Global/Cross-Tenant:**

- **Tenant Management**: Cannot see/create/delete other tenants
- **Public Schema**: Cannot access public schema data
- **Other Tenants**: Cannot see demo2 data or users
- **System Settings**: Cannot modify global Django settings
- **Database Schema**: Cannot create/drop schemas

## Permission Matrix

| Resource | Public Admin | Demo1 Admin | Demo2 Admin | Regular User |
| ---------- | ------------- | ------------- | ------------- | -------------- |
| All Tenants List | ✅ | ❌ | ❌ | ❌ |
| Create New Tenant | ✅ | ❌ | ❌ | ❌ |
| Demo1 Tasks | ✅ | ✅ | ❌ | ✅ (limited) |
| Demo1 Users | ✅ | ✅ | ❌ | ❌ |
| Demo1 Settings | ✅ | ✅ | ❌ | ❌ |
| Demo2 Data | ✅ | ❌ | ✅ | ❌ |
| Global Blog | ✅ | ✅ (read) | ✅ (read) | ✅ (read) |

## Key Principles

1. **Tenant Isolation**: Demo1 admin cannot see demo2 data
2. **Scoped Authority**: Full admin within their tenant only
3. **No Cross-Tenant Access**: Cannot manage other tenants
4. **Limited Global Access**: Can read shared resources (blog) but not manage them

This follows the **principle of least privilege** - each admin gets exactly what they need for their tenant, nothing more.
