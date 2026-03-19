
#!/bin/bash
set -e

# Ensure using docker-desktop context
kubectl config use-context docker-desktop

# Load .env file
export $(cat .env | grep -v '^#' | xargs)

# Create namespace
kubectl create namespace django-multi-tenant-kubernetes --dry-run=client -o yaml | kubectl apply -f -

# Create ConfigMap from .env
kubectl create configmap django-config \
  --from-literal=DJANGO_SETTINGS_MODULE="core.settings" \
  --from-literal=DJANGO_ENV="production" \
  --from-literal=DEBUG="${DEBUG}" \
  --from-literal=ALLOWED_HOSTS="${ALLOWED_HOSTS}" \
  --from-literal=BASE_DOMAIN="${BASE_DOMAIN}" \
  --from-literal=PUBLIC_TENANT_ADMIN_EMAIL="${PUBLIC_TENANT_ADMIN_EMAIL}" \
  --from-literal=DATABASE_HOST="postgres-service" \
  --from-literal=DATABASE_PORT="5432" \
  --from-literal=POSTGRES_HOST="postgres-service" \
  --from-literal=POSTGRES_PORT="5432" \
  --from-literal=SECURE_SSL_REDIRECT="${SECURE_SSL_REDIRECT}" \
  --from-literal=SESSION_COOKIE_SECURE="${SESSION_COOKIE_SECURE}" \
  --from-literal=CSRF_COOKIE_SECURE="${CSRF_COOKIE_SECURE}" \
  --from-literal=EMAIL_BACKEND="${EMAIL_BACKEND}" \
  --from-literal=EMAIL_USE_TLS="${EMAIL_USE_TLS}" \
  --from-literal=EMAIL_HOST="${EMAIL_HOST}" \
  --from-literal=EMAIL_PORT="${EMAIL_PORT}" \
  --from-literal=CONSOLE_LOG_LEVEL="${CONSOLE_LOG_LEVEL:-INFO}" \
  --namespace=django-multi-tenant-kubernetes \
  --dry-run=client -o yaml | kubectl apply -f -

# Create Django Secrets from .env
kubectl create secret generic django-secrets \
  --from-literal=SECRET_KEY="${SECRET_KEY}" \
  --from-literal=EMAIL_HOST_USER="${EMAIL_HOST_USER}" \
  --from-literal=EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
  --from-literal=DEFAULT_FROM_EMAIL="${DEFAULT_FROM_EMAIL}" \
  --from-literal=PUBLIC_TENANT_ADMIN_PASSWORD="${PUBLIC_TENANT_ADMIN_PASSWORD}" \
  --namespace=django-multi-tenant-kubernetes \
  --dry-run=client -o yaml | kubectl apply -f -

# Create Postgres Secrets from .env
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_DB="${POSTGRES_DB}" \
  --from-literal=POSTGRES_USER="${POSTGRES_USER}" \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --namespace=django-multi-tenant-kubernetes \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply the deployment YAML
kubectl apply -f deployment-kubernetes.yaml

echo "Deployment complete!"
echo "Check status: kubectl get pods -n django-multi-tenant-kubernetes"


