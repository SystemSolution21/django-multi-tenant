# Create django-multi-tenant database

## Create the database user with CREATEDB privilege

`CREATE ROLE django_multi_tenant_user WITH LOGIN PASSWORD 'your_secure_password' CREATEDB;`

## Create the database

`CREATE DATABASE django_multi_tenant_db OWNER django_multi_tenant_user;`

## Connect to the django_multi_tenant_db database

`\c django_multi_tenant_db`

## Grant all privileges on the database

`GRANT ALL PRIVILEGES ON DATABASE django_multi_tenant_db TO django_multi_tenant_user;`

## Grant privileges on the public schema (required for django-tenants to create new schemas)

`GRANT ALL PRIVILEGES ON SCHEMA public TO django_multi_tenant_user;`
`GRANT USAGE, CREATE ON SCHEMA public TO django_multi_tenant_user;`

## Grant privileges on all existing tables, sequences, and functions

`GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django_multi_tenant_user;`
`GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django_multi_tenant_user;`
`GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO django_multi_tenant_user;`

## Set default privileges for future objects

`ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO django_multi_tenant_user;`
`ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO django_multi_tenant_user;`
`ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO django_multi_tenant_user;`
