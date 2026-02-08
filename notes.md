# This project is a schema-based multi-tenant application (like Slack, Jira, or Notion) SaaS architecture

## The Public Tenant is the "Landlord"

The Public Schema (lvh.me) acts as the management layer.
It hosts the Landing Page, Sign Up Form, and Global User Database.
Crucially, the Tenant table (the list of all customers) lives only in the Public Schema.

## The Creation Flow

When a user submits the "Onboarding" form on lvh.me, the code (running in the Public context) inserts a new row into the Tenant table.
This triggers django-tenants to create the actual PostgreSQL schema (e.g., mycompany) and run migrations for it.
Finally, the user is redirected to mycompany.lvh.me.

## populate_db vs. Onboarding

populate_db (using tenants.json) is for Seeding: Creating internal/demo tenants or admin accounts manually.
OnboardingView is for Provisioning: Allowing customers to self-service create their own tenants.
Both result in the exact same structure in the database.

## Summary Workflow

- User visits lvh.me:8000/accounts/signup/ (Public Schema).
- User creates account: Added to tenants_user (Global) and linked to Public Tenant (so they can view the onboarding page).
- User fills Onboarding Form:
- App creates new Tenant (e.g., mycompany).
- App creates new Domain (mycompany.lvh.me).
- App switches context to mycompany schema -> Creates "First Project".
- Redirect: User is sent to mycompany.lvh.me:8000/ to start working.

## To Do

- How can I customize the "base.html" template to include a user dropdown menu in the navbar with links to "Profile", "My Tenants", and "Logout"?
- How can I create a "My Profile" page where users can update their first name, last name, and change their password?
