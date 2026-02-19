# Platform-Initiated Tenant Creation Workflow

This document outlines the process, rationale, and technical implementation for a platform provider (a user with "global superuser" privileges) to create new tenants on behalf of customers. This is a common and necessary workflow for many SaaS applications, particularly for managed onboarding and enterprise clients.

## 1. Rationale and Use Cases

While self-service signup is essential, a platform-initiated workflow is critical for several real-world scenarios:

- **Managed Onboarding:** For enterprise clients, an account manager or sales engineer often sets up the initial tenant, configures integrations, and pre-populates data as part of a "white-glove" service.
- **Sales & Demonstrations:** The sales team needs the ability to quickly spin up new, isolated tenants for product demonstrations tailored to specific prospects.
- **Internal Testing:** QA and development teams require a method to create tenants for testing new features or replicating customer-reported issues in a controlled environment.
- **Reseller/Partner Models:** If the SaaS operates with partners, those partners need an interface to provision tenants for their own end-users.

## 2. The User Workflow

The process is designed to be secure and straightforward, initiated from the Django Admin interface.

- 1.**Navigate to Tenant Management:** The global superuser logs into the admin panel (`/admin/`) and navigates to the "Tenants" list.
- 2.**Initiate Provisioning:** Instead of a standard "Add Tenant" button (which is disabled to prevent misconfiguration), the user clicks a custom **"Provision New Tenant"** button.
- 3.**Complete the Provisioning Form:** The user is presented with a dedicated form that requires all necessary information to create a complete and valid tenant and owner account:
  - Tenant Name (e.g., "Client Corp")
  - Subdomain (e.g., "clientcorp")
  - Owner's First Name
  - Owner's Last Name
  - Owner's Email Address
  - A secure initial Password for the owner
  - Password Confirmation

- 4.**Submit and Create:** Upon submission, the system performs the following actions within a single, atomic database transaction:
  - Validates the form data (e.g., checks for password match, unique subdomain).
  - Creates a new `User` record for the tenant owner.
  - Calls the `provision_tenant` utility to create the `Tenant` instance, the PostgreSQL schema, and the primary `Domain`.

- 5.**Confirmation:** The superuser is redirected back to the tenant list with a success message.

## 3. Post-Provisioning: Customer Onboarding

After the platform provider has created the tenant, the new tenant owner's journey begins.

1. **Email Notification:** The system should trigger an email to the new owner. This email contains:
    - A welcome message.
    - The URL to their new tenant's login page (e.g., `http://clientcorp.lvh.me:8000`).
    - The temporary password set by the admin.
    - **Crucially**, a clear instruction that they **must change this password** upon their first login.
2. **First Login and Forced Password Reset:**
    - The user logs in with their email and the temporary password.
    - The application should immediately detect that this is their first login with a temporary credential and redirect them to a mandatory "Change Password" form.
    - This ensures the temporary password is invalidated and the user's account is secured with a password only they know.

## 4. Technical Implementation Details

### `tenants/admin.py`

- The `TenantAdmin` class disables the default `has_add_permission` to prevent direct, incomplete tenant creation.
- It defines a custom URL and view (`provision_view`) that renders the `ProvisionTenantForm`.
- The `provision_view` handles form validation and calls the `create_tenant` utility function.

### `tenants/utils.py`

- The `create_tenant` function is the core of the logic. It encapsulates the creation of the `User` (if they don't exist) and the call to `django-tenant-users`'s `provision_tenant` task, ensuring both are created correctly within a transaction.

### Security Considerations

- **Separation of Concerns:** The global superuser who provisions the tenant is **not** automatically added as a member of that tenant. This is a critical security boundary. It prevents a tenant's admin from potentially modifying or deleting the global superuser's account.
- **Impersonation (Hijack):** For support and administration, the global superuser should rely on the "Login as" (impersonation) feature to access a tenant's environment, rather than being a permanent member.
- **Temporary Password Handling:**
  - **Generation:** Passwords should be strong and randomly generated.
  - **Transmission:** Email is standard but not perfectly secure. The risk is mitigated by the mandatory password reset on first login.
  - **Expiration:** The temporary password or the "set password" link should have a short expiration time (e.g., 24-48 hours).
- **Audit Trail:** All provisioning actions are logged using `structlog`, creating an audit trail of who created which tenant and when.

This workflow provides a robust, secure, and practical solution for managing tenant creation in a real-world SaaS environment.
