The `admin@demo1.localhost` should have **tenant-scoped admin privileges** - full control within their tenant but no access to other tenants or global system management.

## Recommended Privileges for `admin@demo1.localhost`

### ✅ **SHOULD HAVE ACCESS TO:**

**Within Demo1 Tenant Schema:**

- **User Management**: Create/edit/delete users within demo1 tenant
- **Tasks App**: Full CRUD on projects and tasks in demo1 schema
- **Django Admin**: Access to `/admin/` for demo1-specific models
- **API Endpoints**: Full access to `/api/tasks/`, `/api/projects/` in demo1 context
- **Tenant Settings**: Modify demo1 tenant name, preferences (but not schema_name)

### ❌ **SHOULD NOT HAVE ACCESS TO:**

**Global/Cross-Tenant:**

- **Tenant Management**: Cannot see/create/delete other tenants
- **Public Schema**: Cannot access public schema data
- **Other Tenants**: Cannot see demo2 data or users
- **System Settings**: Cannot modify global Django settings
- **Database Schema**: Cannot create/drop schemas

## Implementation Example

````python path=tenants/views.py mode=EDIT
class TenantSelfUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Allow tenant admin to update their own tenant details only"""
    model = Tenant
    fields = ["name"]  # Not schema_name!
    template_name = "tenants/tenant_self_update.html"
    
    def test_func(self):
        # Only tenant admin can edit their own tenant
        return (
            self.request.user.is_staff and 
            connection.schema_name != 'public'
        )
    
    def get_object(self):
        # Get current tenant from schema context
        return Tenant.objects.get(schema_name=connection.schema_name)
````

## Permission Matrix

| Resource | Public Admin | Demo1 Admin | Demo2 Admin | Regular User |
|----------|-------------|-------------|-------------|--------------|
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
