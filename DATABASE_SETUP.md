
# PostgreSQL database setup for django-multi-tenant project

## Prerequisites

- PostgreSQL database server is installed and running
- psql command-line tool is installed and available in the PATH

## Create django-multi-tenant database

- ### Open psql command-line tool as the postgres user

  - `psql -U postgres`

    Enter the password for the postgres user when prompted.

- ### Create the database user with CREATEDB privilege

  - `CREATE ROLE django_multi_tenant_user WITH LOGIN PASSWORD 'your_secure_password' CREATEDB;`

- ### Create the database

  - `CREATE DATABASE django_multi_tenant_db OWNER django_multi_tenant_user;`

- ### Connect to the django_multi_tenant_db database

  - `\c django_multi_tenant_db`

- ### Grant all privileges on the database

  - `GRANT ALL PRIVILEGES ON DATABASE django_multi_tenant_db TO django_multi_tenant_user;`

- ### Grant privileges on the public schema (required for django-tenants to create new schemas)

  - `GRANT ALL PRIVILEGES ON SCHEMA public TO django_multi_tenant_user;`
  - `GRANT USAGE, CREATE ON SCHEMA public TO django_multi_tenant_user;`

- ### Grant privileges on all existing tables, sequences, and functions

  - `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django_multi_tenant_user;`
  - `GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django_multi_tenant_user;`
  - `GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO django_multi_tenant_user;`

- ### Set default privileges for future objects

  - `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO django_multi_tenant_user;`
  - `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO django_multi_tenant_user;`
  - `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO django_multi_tenant_user;`

## Verify the database inside the db container

Navigate to project directory in terminal and run the following command. This will give  a command prompt inside the db container.
`docker-compose exec db sh`

- `psql -U django_multi_tenant_user -d django_multi_tenant_db` Enter the password for the django_multi_tenant_user when prompted.

- `\c django_multi_tenant_db` Connect to the django_multi_tenant_db database

- `\dt` list all tables in the public schema

- `\df` list all functions in the public schema

- `\dn` list all schemas in the database

- `SELECT * FROM tenants_user;` Query the tenants_user table

- `SET search_path TO demo;` Switch to the demo schema

- `SET search_path TO public;` Switch to the public schema

- `\q` Quit psql

## Creating Backup of the database

This command will connect to the database inside  db container and dump its entire contents, including all tenant schemas, into a single SQL file on  local machine.

Run this command from  project's root directory (where  docker-compose.yml is located):

- `docker-compose exec db pg_dump -U django_multi_tenant_user django_multi_tenant_db > backup.sql`

Command Breakdown:

- `docker-compose exec -T db`: Executes a command inside the `db` service container. The `-T` flag is important as it disables the pseudo-tty, which is necessary for clean input/output redirection.
- `pg_dump`: The standard PostgreSQL utility for creating database backups.
- `-U django_multi_tenant_user`: Specifies the database user to connect with (.env file).
- `-d django_multi_tenant_db`: Specifies the database name to back up.
- `> backup.sql`: Redirects the output of the pg_dump command to a new file named backup.sql on  host machine.
After running this,  will have a backup.sql file in  project directory. This file is a complete snapshot of  database at that moment.

## Restoring the database from Backup

Restoring involves piping the `backup.sql` file into the `psql` command inside the container. For a clean restore, it's best practice to first drop and recreate the database.

- ### Drop and recreate the database

    This ensures restoring into a completely empty database, avoiding any conflicts.

  - `docker-compose stop web` Stop the web container to release any connections to the database

  - `docker-compose exec db dropdb -U django_multi_tenant_user django_multi_tenant_db` Drop the existing database

  - `docker-compose exec db createdb -U django_multi_tenant_user django_multi_tenant_db` Create a new database

- ### Restore the database

    This command reads local `backup.sql` file and sends its contents to the `psql` tool inside the `db` container, which executes the SQL commands to rebuild the schemas, tables, and data.

  - `cat backup.sql | docker-compose exec -T db psql -U django_multi_tenant_user -d django_multi_tenant_db`

Command Breakdown:

- `cat backup.sql`: Reads the content of backup file to standard output.
- `|`: The "pipe" operator, which sends the output of the cat command as the input to the next command.
- `docker-compose exec -T db psql ...`: Executes the psql interactive terminal inside the `db` container. container. When run this way, `psql` reads from its standard input and executes the SQL it receives.

- ### Restart the web container

    Once the restore is complete, start the web container again.

  - `docker-compose up -d web`

## Important Considerations

- Security: Store `backup.sql` files in a secure location, as they contain all application's data.
- Automation: For production environments, should user script and automate this backup process to run on a regular schedule (e.g., daily) using a cron job or a similar task scheduler.
- Testing: Regularly test restore process in a staging environment to ensure backups are valid and can be recovered successfully.
