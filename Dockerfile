# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Copy uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies required for PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project configuration
COPY pyproject.toml ./

# --system installs into the system python environment
RUN uv pip install --system -r pyproject.toml

# Copy the entrypoint script and ensure it has correct line endings and is executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Copy application code
COPY . .

# Create a non-root user for security
RUN addgroup --system app && adduser --system --group app

# Create directory for static files and set permissions
RUN mkdir -p staticfiles media && chown -R app:app /app

# Switch to non-root user
USER app

# Set the entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Expose the port
EXPOSE 8000

# Define the command to run the application
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
