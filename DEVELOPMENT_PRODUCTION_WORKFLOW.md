# Development and Production Workflows

This document outlines the workflows for developing, testing, and running the `django-multi-tenant` application in different environments using Docker.

## Prerequisites

Ensure you have the following installed locally:

- **Docker** and **Docker Compose** (Docker Desktop recommended for Windows/Mac)
- **Git**
- **Python** 3.13
- **PostgreSQL** 17
- **uv**

## Project Structure

``` project structure
django-multi-tenant/
│
├── accounts/                 # User authentication and registration
|   ├── migrations/           # Database migrations for the accounts app
|   |    ├── __init__.py      # Initialization for migrations
|   |    └── 0001_initial.py  # Initial migration file
|   |
|   ├── templates/accounts/   # HTML templates for the accounts app
|   ├── __init__.py # Initialization for the accounts app
|   ├── admin.py    # Admin interface configuration
|   ├── apps.py     # App configuration
|   ├── forms.py    # Forms for user registration and authentication
|   ├── models.py   # User model and related models
|   ├── signals.py  # Signals for user actions
|   ├── tests.py    # Tests for user authentication and registration
|   ├── urls.py     # URL patterns for user authentication and registration
|   └── views.py    # Views for user authentication and registration
│
├── blog/                       # Blog application
|   ├── migrations/             # Database migrations for the blog app
|   |    ├── __init__.py        # Initialization for migrations
|   |    └── 0001_initial.py    # Initial migration file
|   |
|   ├── management/             # Custom management commands for the blog app
|   |    ├── commands/          # Management commands
|   |    |    └── __init__.py   # Initialization for management commands
|   |    |
|   |    └── __init__.py        # Initialization for management
|   |
|   ├── static/blog/                        # Static files for the blog app
|   ├── templates/                          # HTML templates for the blog app
|   |    ├── blog/                          # Templates for the blog app
|   |    ├── article_confirm_delete.html    # Template for deleting an article
|   |    ├── article_detail.html            # Template for viewing an article
|   |    ├── article_form.html              # Template for creating or editing an article
|   |    └── article_list.html              # Template for displaying a list of articles
|   |
|   ├── __init__.py         # Initialization for the blog app
|   ├── admin.py            # Admin interface configuration
|   ├── apps.py             # App configuration
|   ├── Blog_Readme.md      # Readme file for the blog app
|   ├── forms.py            # Forms for the blog app
|   ├── models.py           # Blog models
|   ├── serializers.py      # Serializers for the blog app
|   ├── tests.py            # Tests for the blog app
|   ├── urls.py             # URL patterns for the blog app
|   └── views.py            # Views for the blog app
│
├── core/                       # Project-wide settings, URLs, and utilities
|   ├── __init__.py             # Initialization for the core app
|   ├── admin.py                # Admin interface configuration
|   ├── apps.py                 # App configuration
|   ├── asgi.py                 # ASGI configuration for the project
|   ├── context_processors.py   # Context processors for the core app
|   ├── middleware.py           # Custom middleware for the core app
|   ├── models.py               # Core models
|   ├── settings.py             # Project settings
|   ├── sites.py                # Custom admin site configuration
|   ├── urls_public.py          # URL patterns for the public schema
|   ├── urls.py                 # URL patterns for the core app
|   ├── views.py                # Views for the core app
|   └── wsgi.py                 # WSGI configuration for the project
│
├── logs/                       # Log files
|   ├── app.log                 # Application log file
|   └── error.log               # Error log file
|
├── media/                      # User-uploaded files
├── static/                     # Static files (CSS, JS, images)
|   ├── core/                   # Static files for the core app
|   |    ├── favicon.ico        # Favicon file for the core app
|   |    ├── SaaS.svg           # Image files for the core app
|   |    ├── style.css          # CSS files for the core app
|   |    └── scripts.js         # JavaScript files for the core app
|   | 
|   └── favicon.ico             # Favicon file
|
├── staticfiles/                # Collected static files for production
|
├── tasks/                      # Task management application
|   ├── migrations/             # Database migrations for the tasks app
|   |    ├── __init__.py        # Initialization for migrations
|   |    └── 0001_initial.py    # Initial migration file
|   |
|   ├── static/tasks/           # Static files for the tasks app
|   |
|   ├── templates/                             # HTML templates for the tasks app
|   |    └── tasks/                            # Templates for the tasks app
|   |        ├── project_confirm_delete.html   # Template for deleting a project
|   |        ├── project_detail.html           # Template for viewing a project
|   |        ├── project_form.html             # Template for creating or editing a project
|   |        ├── project_list.html             # Template for displaying a list of projects
|   |        ├── task_confirm_delete.html      # Template for deleting a task
|   |        ├── task_detail.html              # Template for viewing a task
|   |        ├── task_form.html                # Template for creating or editing a task
|   |        └── task_list.html                # Template for displaying a list of tasks
|   |
|   ├── __init__.py             # Initialization for the tasks app
|   ├── admin.py                # Admin interface configuration
|   ├── apps.py                 # App configuration
|   ├── forms.py                # Forms for the tasks app
|   ├── models.py               # Task models
|   ├── serializers.py          # Serializers for the tasks app
|   ├── Tasks_Enhancement.md    # Enhancement file for the tasks app
|   ├── Tasks_Readme.md         # Readme file for the tasks app
|   ├── tests.py                # Tests for the tasks app
|   ├── urls.py                 # URL patterns for the tasks app
|   └── views.py                # Views for the tasks app
│
├── templates/                              # HTML templates
|   ├── admin/                              # Templates for the admin interface
|   |   ├── tenants/                        # Templates for the tenants app
|   |   |   ├── tenant/                     # Templates for the tenant model
|   |   |   |   ├── change_list.html        # Custom change list template
|   |   |   |   └── provision_form.html     # Custom provision form template
|   |   |   |
|   |   |   └── users/                                  # Templates for the users app
|   |   |      └── delete_selected_confirmation.html    # Custom delete confirmation template
|   |   |
|   |   └── base_site.html      # Custom admin base template
|   |   
|   ├── core/               # Templates for the core app
|   |    └── index.html     # Home page template for the public schema
|   |
|   ├── registration/                      # Templates for the registration app
|   |    ├── login.html                     # Login page template
|   |    ├── onboarding.html                # Onboarding page template
|   |    ├── password_reset_confirm.html    # Password reset confirmation page template
|   |    ├── password_reset_done.html       # Password reset done page template
|   |    ├── password_reset_email.html      # Password reset email template
|   |    ├── password_reset_form.html       # Password reset form template
|   |    └── signup.html                    # Signup page template
|   |
|   ├── 403.html                # 403 Forbidden error page
|   ├── 404.html                # 404 Not Found error page
|   ├── 500.html                # 500 Internal Server Error error page
|   └── base.html               # Base template for the project
│
├── tenants/           # Tenant management system
|   ├── data/                         # Data files for the tenants app
|   |    └── tenants.json              # JSON file for tenant data
|   |
|   ├── management/                   # Management commands for the tenants app
|   |    └── commands/                  # Management commands
|   |       ├── __init__.py                 # Initialization for management commands
|   |       ├── cleanup_invitations.py      # Cleanup invitations management command(debugging purposes)
|   |       ├── cleanup_orphaned_users.py   # Cleanup orphaned users management command(debugging purposes)
|   |       ├── force_delete_tenant.py      # Force delete a tenant management command(debugging purposes)
|   |       ├── tenant_privileges.py        # Demote a user from superuser and assign tenant-specific permissions management command(debugging purposes)
|   |       ├── project_global_search.py # Search for blog articles, projects and tasks across all tenant schemas and the public schema management command(debugging purposes)
|   |       ├── populate_db.py         # Populate database management command
|   |       └── init_public_tenant.py  # Initialize public tenant management command
|   |
|   |
|   ├── migrations/            # Database migrations for the tenants app
|   |    ├── __init__.py        # Initialization for migrations
|   |    └── 0001_initial.py    # Initial migration file
|   |
|   ├── static/tenants/        # Static files for the tenants app
|   |
|   ├── templates/                          # HTML templates for the tenants app
|   |    ├── tenants/                        # Templates for the tenants app
|   |    |   ├── accept_invitation.html      # Template for accepting an invitation
|   |    |   ├── decline_invitation.html     # Template for declining an invitation
|   |    |   ├── tenant_confirm_delete.html  # Template for deleting a tenant
|   |    |   ├── tenant_detail.html          # Template for viewing a tenant
|   |    |   ├── tenant_form.html            # Template for creating or editing a tenant
|   |    |   ├── tenant_list.html            # Template for displaying a list of tenants
|   |    |   ├── tenant_transfer_ownership.html     # Template for transferring ownership of a tenant
|   |    |   ├── user_confirm_remove_delete.html    # Template for confirming removal of a user
|   |    |   ├── user_edit.html                # Template for editing a user
|   |    |   ├── user_invite.html              # Template for inviting a user
|   |    |   └── user_list.html                # Template for listing users
|   |    |
|   |    └── admin/                         # Templates for the admin interface
|   |        └── hijack_confirm.html         # Template for confirming hijack
|   |
|   ├── templatetags/                   # Template tags for the tenants app
|   |    ├── __init__.py                 # Initialization for template tags
|   |    └── tenant_tags.py              # Template tags for the tenants app
|   |
|   ├── __init__.py            # Initialization for the tenants app
|   ├── admin.py               # Admin interface configuration
|   ├── api_views.py           # API views for the tenants app
|   ├── apps.py                # App configuration
|   ├── forms.py               # Forms for the tenants app
|   ├── mixins.py              # Mixins for the tenants app
|   ├── models.py              # Tenant models
|   ├── serializers.py         # Serializers for the tenants app
|   ├── Tenants_Entity_Relationships_Readme.md # Entity relationships documentation for the tenants app
|   ├── Tenants_Privileges.md  # Privileges documentation for the tenants app
|   ├── Tenants_Readme.md      # Readme file for the tenants app
|   ├── tests.py               # Tests for the tenants app
|   ├── urls.py                # URL patterns for the tenants app
|   ├── utils/                 # Utility modules for tenants app
|   └── views.py               # Views for the tenants app
│
├── utils/             # Utility modules
|   ├── __init__.py    # Initialization for the utils package
|   └── logger.py      # Logging configuration
│
├── .dockerignore      # Docker ignore file
├── .env               # Environment variables
├── .env.example       # Example .env file
├── .gitignore         # Git ignore file
├── .python-version    # Python version file for uv
├── database.txt       # Database configuration file(munally create the database and user from this file)
├── DEVELOPMENT_PRODUCTION_WORKFLOW.md # Development and production workflow documentation
├── docker-compose.override.yml # Docker Compose override configuration for development
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile         # Docker image definition
├── entrypoint.sh      # Docker entrypoint script
├── manage.py          # Django management script
├── PLATFORM-INITIATED-TENANT-CREATION.md # Platform-initiated tenant creation documentation
├── pyproject.toml     # Python project configuration for uv
├── README.md          # Project README file
├── requirements.txt   # Python dependencies
├── TENANT_AUDIT_CHECKLIST.md # Tenant audit checklist documentation
└── uv.lock            # uv lock file
```

## Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone <https://github.com/SystemSolution21/django-multi-tenant.git>
   cd django-multi-tenant
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the project root with the required credentials (database, email, etc.).

## 1. Development Workflow

The development environment is designed for rapid iteration. It uses Django's built-in `runserver` with live code reloading.

### Starting the Environment

To start the development environment, simply run:

```bash
docker-compose up
```

**What happens:**

- Docker Compose automatically merges `docker-compose.yml` (base) and `docker-compose.override.yml` (dev overrides).
- **Volume Mounting:** Your local source code is mounted to `/app` inside the container. Changes you make locally are immediately reflected in the container.
- **Command:** The container runs `python manage.py runserver 0.0.0.0:8000`.
- **Environment:** `DJANGO_ENV` is set to `development`, skipping `collectstatic` to speed up startup.

### Accessing the Application

- **Public Domain:** <http://lvh.me:8000>
- **Tenant Subdomains:** `http://<tenant_slug>.lvh.me:8000` (e.g., `http://demo.lvh.me:8000`)

### Common Development Tasks

Since the code is mounted, you can run management commands inside the running container:

**Access the container shell:**

```bash
docker-compose exec web bash
```

**Run Migrations (Shared & Tenants):**

```bash
docker-compose exec web python manage.py migrate_schemas
```

---

## 2. Production Workflow

The production environment is optimized for performance and security. It uses **Gunicorn** as the application server and does not mount local code volumes.

### Running in Production Mode Locally

To simulate the production environment locally, you must explicitly tell Docker Compose to ignore the override file:

```bash
docker-compose -f docker-compose.yml up --build
```

**What happens:**

- **No Volume Mounting:** The code inside the container is "baked in" during the build process. Changes to local files will **not** affect the running container until you rebuild.
- **Command:** The container runs the `CMD` defined in the `Dockerfile`: `gunicorn core.wsgi:application ...`.
- **Environment:** `DJANGO_ENV` is set to `production`.
- **Static Files:** The `entrypoint.sh` script detects the production environment and automatically runs `python manage.py collectstatic --noinput --clear`.

### Deployment Configuration

Ensure your `.env` file (or environment variables in your deployment platform) is configured for production:

- `DEBUG=False`
- `SECRET_KEY`: Set to a strong, random string.
- `ALLOWED_HOSTS`: Set to your actual domain names.
- `EMAIL_BACKEND`: Use an SMTP backend (e.g., SendGrid, AWS SES, or Gmail) instead of the Console backend.

---

## 3. Docker Configuration Structure

The project uses a layered Docker Compose approach:

1. **`Dockerfile`**:
    - **Multi-stage build**: Uses a builder stage to compile dependencies and a final stage for the runtime, keeping the image size small.
    - **Security**: Runs as a non-root user (`app`).
    - **Entrypoint**: Sets `/app/entrypoint.sh` as the entrypoint.

2. **`entrypoint.sh`**:
    - Runs database migrations (`migrate_schemas`) on every startup.
    - Initializes the public tenant (`init_public_tenant`).
    - Conditionally runs `collectstatic` only if `DJANGO_ENV=production`.

3. **`docker-compose.yml` (Base/Production)**:
    - Defines the services (`db`, `web`).
    - Sets production defaults (Gunicorn, `DJANGO_ENV=production`).

4. **`docker-compose.override.yml` (Development)**:
    - Overrides the `web` service to use `runserver`.
    - Mounts the local directory `.` to `/app`.
    - Sets `DJANGO_ENV=development`.
