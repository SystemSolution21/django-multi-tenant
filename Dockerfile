# ----------------- Stage 1: Builder -----------------
# This stage installs dependencies into a virtual environment.
FROM python:3.13-slim AS builder

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # This prevents installing packages into the global site-packages
    VIRTUAL_ENV=/opt/venv

# Install system dependencies required for PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment using uv
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy dependency file and install into the venv
WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --no-cache-dir -r pyproject.toml

# ----------------- Stage 2: Final Image -----------------
# This stage creates the final, smaller production image.
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set work directory
WORKDIR /app

# Copy application code and entrypoint
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Create directory for static files and set permissions
RUN mkdir -p staticfiles media && chown -R app:app /app

# Switch to non-root user
USER app

# Activate the virtual environment by adding it to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Set the entrypoint using an absolute path
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose the port
EXPOSE 8000

# Define the command to run the application
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "60"]
