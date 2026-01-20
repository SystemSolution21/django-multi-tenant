# Tenant Entity Relationships & Lifecycle

This document outlines the architectural relationships between Users, Tenants, and Domains within the `django-tenants` and `django-tenant-users` ecosystem, as well as the implications of data deletion.

## 1. Entity Relationships

The architecture uses a **Shared User / Isolated Tenant** model.

### User (Global)

* **Location:** Lives in the `public` schema.
* **Definition:** Inherits from `UserProfile` (`tenants/models.py`).
* **Relation:** A User can belong to **many** Tenants. They authenticate globally but have specific permissions per tenant.
* **Code Reference:** In `populate_db.py`, `tenant_owner` is created once and then passed to `provision_tenant`.

### Tenant (Container)

* **Location:** Lives in the `public` schema (metadata) but **owns** a specific PostgreSQL schema (e.g., `demo1`) where actual app data resides.
* **Definition:** Inherits from `TenantBase` (`tenants/models.py`).
* **Relation:** A Tenant has **many** Users (via a permission table managed by `django-tenant-users`) and **many** Domains (one-to-many relationship).

### Domain (EntryPoint)

* **Location:** Lives in the `public` schema.
* **Definition:** Inherits from `DomainMixin` (`tenants/models.py`).
* **Relation:** A Domain belongs to **one** Tenant(ForeignKey). It acts as the routing key (e.g., `demo1.localhost` -> `demo1` schema). Multiple domains can point to the same tenant (e.g., `demo1.com` and `demo1.net` both route to the `demo1` schema).

## 2. Deletion Restrictions & Behavior

Here is the impact of deleting specific entities based on standard `on_delete` behaviors:

| Action | Effect on Tenant | Effect on Domain | Effect on User | Effect on Schema |
| :--- | :--- | :--- | :--- | :--- |
| **Delete Tenant** | **N/A** | **Deleted** (Cascade) | **Unaffected** | **Dropped** (Data Lost) |
| **Delete Domain** | Unaffected | **N/A** | Unaffected | Unaffected |
| **Delete User** | Unaffected | Unaffected | **N/A** | Unaffected |

### Detailed Impact

* **Deleting a Tenant (Highest Impact):**
  * Because `Domain` has a ForeignKey to `Tenant` with `on_delete=models.CASCADE`, deleting a Tenant **automatically deletes all associated Domains**.
  * It triggers a signal to **drop the PostgreSQL schema**, permanently erasing all data inside that tenant (e.g., blog posts, orders).
  * It **does not** delete the Users. The users simply lose their link/permissions to that specific tenant.

* **Deleting a Domain:**
  * The Tenant and Schema remain intact, but the tenant becomes inaccessible via HTTP requests for that specific URL.

* **Deleting a User:**
  * The User is removed from the `public` schema. They lose access to **all** tenants they were part of.
  * Tenant data created by that user (inside the tenant schemas) usually remains, depending on how specific app models handle `author=ForeignKey(User)`.

## 3. Priority Steps for Deletion

When managing data cleanup, the order of operations matters to avoid orphaned records or database errors.

### Scenario A: Full Customer Offboarding (Recommended)

If you want to remove a client completely:

1. **Delete the Tenant.**
    * *Why?* This is the "root" action. It automatically cleans up the Domains and drops the Schema.
    * *Note:* You generally do **not** delete the User immediately, as that User might own other tenants or be a shared staff member.

### Scenario B: Hard Reset (Development)

If you are resetting the environment (like in `populate_db.py`):

1. **Drop Database / Schema:** The script uses `drop_and_recreate_db` to nuke the entire database.
2. **Create Public Tenant:** Essential first step (`create_public_tenant`).
3. **Create Users:** Users must exist before they can be assigned to private tenants.
4. **Provision Tenants:** Creates the Tenant and Domain, and links the existing User.

### Scenario C: Removing a Specific Route

1. **Delete the Domain.**
    * *Why?* If you just want to change `demo1.localhost` to `app.localhost`, you delete the old domain and create a new one linked to the *same* tenant.

## 4. Summary of Hierarchy

```text
User (Global)
  ↕ (Many-to-Many Permission Link)
Tenant (Schema Owner)
  ⬇ (One-to-Many Cascade)
Domain (URL Routing)
```
