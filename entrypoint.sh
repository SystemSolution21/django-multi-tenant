#!/bin/sh
set -e

# Run database migrations and initial setup
python manage.py migrate_schemas --noinput
python manage.py init_public_tenant

# Collect static files only in production
if [ "$DJANGO_ENV" = "production" ]; then
    echo "=== Collecting static files for production ==="
    python manage.py collectstatic --noinput --clear
fi

# Execute the main command (e.g., gunicorn or runserver)
exec "$@"
