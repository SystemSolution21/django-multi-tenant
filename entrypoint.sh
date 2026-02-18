#!/bin/sh
set -e

# Run database migrations and initial setup
python manage.py migrate_schemas --noinput
python manage.py init_public_tenant

# Collect static files
python manage.py collectstatic --noinput --clear

# Execute the main command (e.g., gunicorn or runserver)
exec "$@"
