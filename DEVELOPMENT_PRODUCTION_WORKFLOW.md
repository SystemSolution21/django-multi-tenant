# Development and Production Workflows

This document outlines the workflows for developing, testing, and running the `django-multi-tenant` application in different environments using Docker.

## Prerequisites

Ensure you have the following installed locally:

- **Docker** and **Docker Compose** (Docker Desktop recommended for Windows/Mac)
- **Git**
- **Python** 3.13
- **PostgreSQL** 17
- **uv**

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
