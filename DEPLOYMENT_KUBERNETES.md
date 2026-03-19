# Kubernetes Deployment Guide

This guide covers deploying the `django-multi-tenant` application to Kubernetes with multi-tenant subdomain routing.

## Prerequisites

- **Docker Desktop** with Kubernetes enabled (or kind/minikube)
- **kubectl** configured
- **Docker image** pushed to registry: `systemsolution21/django-multi-tenant:v0.1.0`
- **`.env` file** with required environment variables

## Architecture

- **Postgres**: Single replica with persistent storage (5Gi PVC)
- **Django**: 2-5 replicas (HPA-managed) running Gunicorn
- **NGINX Ingress**: Wildcard routing for tenant subdomains
- **Services**: ClusterIP for Postgres, LoadBalancer for Django

## Deployment Steps

### 1. Switch to Docker Desktop Context

```bash
kubectl config use-context docker-desktop
```

### 2. Deploy Infrastructure

```bash
# Run deployment script (creates namespace, configmaps, secrets, deployments)
./deploy-k8s.sh
```

**What it does:**

- Creates `django-multi-tenant-kubernetes` namespace
- Creates ConfigMap from `.env` (non-sensitive config)
- Creates Secrets from `.env` (passwords, keys)
- Applies `deployment-kubernetes.yaml` (Postgres + Django deployments)

### 3. Install NGINX Ingress Controller

```bash
# Install NGINX Ingress for kind/Docker Desktop
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for readiness
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### 4. Deploy Ingress Resource

```bash
# Apply ingress for wildcard subdomain routing
kubectl apply -f ingress.yaml
```

### 5. Verify Deployment

```bash
# Check all resources
kubectl get all -n django-multi-tenant-kubernetes

# Check ingress
kubectl get ingress -n django-multi-tenant-kubernetes

# Check pod logs
kubectl logs -f deployment/django-multi-tenant -n django-multi-tenant-kubernetes
```

## Accessing the Application

- **Public tenant**: `http://lvh.me`
- **Tenant subdomains**: `http://<tenant-slug>.lvh.me` (e.g., `http://demo.lvh.me`)

The NGINX Ingress controller routes all `*.lvh.me` requests to Django with the correct `Host` header, enabling tenant resolution.

## Key Configuration Details

### Health Probes

Uses **TCP probes** instead of HTTP to avoid 404 errors from tenant routing:

```yaml
livenessProbe:
  tcpSocket:
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  tcpSocket:
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Horizontal Pod Autoscaler

Automatically scales Django pods (2-5 replicas) based on CPU:

```yaml
minReplicas: 2
maxReplicas: 5
targetCPUUtilizationPercentage: 70
```

### Init Container

Waits for Postgres to be ready before starting Django:

```yaml
initContainers:
  - name: db-wait
    image: postgres:17-alpine
    command: ["pg_isready", "-h", "postgres-service"]
```

## Common Operations

### View Logs

```bash
# Django logs
kubectl logs -f deployment/django-multi-tenant -n django-multi-tenant-kubernetes

# Postgres logs
kubectl logs -f deployment/postgres -n django-multi-tenant-kubernetes
```

### Scale Manually

```bash
kubectl scale deployment django-multi-tenant --replicas=3 -n django-multi-tenant-kubernetes
```

### Update Deployment

```bash
# After pushing new image
kubectl set image deployment/django-multi-tenant \
  django=systemsolution21/django-multi-tenant:v0.2.0 \
  -n django-multi-tenant-kubernetes

# Or re-run deployment script
./deploy-k8s.sh
```

### Restart Pods

```bash
kubectl rollout restart deployment/django-multi-tenant -n django-multi-tenant-kubernetes
```

### Access Pod Shell

```bash
kubectl exec -it deployment/django-multi-tenant -n django-multi-tenant-kubernetes -- bash
```

### Run Django Management Commands

```bash
# Migrations
kubectl exec -it deployment/django-multi-tenant -n django-multi-tenant-kubernetes -- \
  python manage.py migrate_schemas

# Create superuser
kubectl exec -it deployment/django-multi-tenant -n django-multi-tenant-kubernetes -- \
  python manage.py createsuperuser
```

## Troubleshooting

### Pods in CrashLoopBackOff

```bash
# Check pod events
kubectl describe pod <pod-name> -n django-multi-tenant-kubernetes

# Check logs
kubectl logs <pod-name> -n django-multi-tenant-kubernetes
```

### Database Connection Issues

```bash
# Verify Postgres is running
kubectl get pods -l app=postgres -n django-multi-tenant-kubernetes

# Check Postgres logs
kubectl logs deployment/postgres -n django-multi-tenant-kubernetes

# Test connection from Django pod
kubectl exec -it deployment/django-multi-tenant -n django-multi-tenant-kubernetes -- \
  pg_isready -h postgres-service -p 5432
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n django-multi-tenant-kubernetes

# Check NGINX controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace django-multi-tenant-kubernetes

# Delete ingress controller (optional)
kubectl delete namespace ingress-nginx
```

## Production Considerations

For production deployments:

1. **Use managed Kubernetes** (EKS, GKE, AKS)
2. **Configure real domain** with DNS wildcard (`*.yourdomain.com`)
3. **Enable TLS/SSL** with cert-manager
4. **Use managed database** (RDS, Cloud SQL) instead of in-cluster Postgres
5. **Configure resource limits** based on load testing
6. **Set up monitoring** (Prometheus, Grafana)
7. **Configure backup strategy** for persistent volumes
8. **Use secrets management** (Vault, AWS Secrets Manager)
