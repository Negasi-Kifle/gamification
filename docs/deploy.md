# Deployment Guide

Per technical guideline §12 - After each deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Deployment Steps](#deployment-steps)
- [Health Checks](#health-checks)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Infrastructure

- PostgreSQL 16+
- Kafka (or Redpanda) with Schema Registry
- Docker runtime (for containerized deployment)
- Kubernetes cluster (for production)

### Required Secrets

Ensure these are configured in your deployment environment (never in code):

| Secret | Description | Example |
|--------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_PASSWORD` | PostgreSQL password | - |
| `KAFKA_SASL_PASSWORD` | Kafka SASL password (if using SASL) | - |

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | (see above) |
| `DB_NAME` | Database name | `gamification` |
| `POSTGRES_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | - |
| `DB_HOST` | Database host | `postgres.example.com` |
| `DB_PORT` | Database port | `5432` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | `kafka-1:9092,kafka-2:9092` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_DEBUG` | Debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | (empty) |
| `LOG_LEVEL` | Log level | `INFO` |
| `SERVICE_NAME` | Service name for logs | `gamification` |
| `SCHEMA_REGISTRY_URL` | Schema Registry URL | - |
| `GRPC_PORT` | gRPC server port | `50051` |
| `GRPC_MAX_WORKERS` | gRPC worker threads | `10` |
| `SCHEDULER_SERVICE_URL` | Scheduler service URL | - |
| `JAEGER_ENDPOINT` | Jaeger collector URL | - |

---

## Deployment Steps

### 1. Pre-deployment Checklist

- [ ] All tests pass in CI
- [ ] Migration linter passes
- [ ] Docker image built and pushed
- [ ] Environment variables configured
- [ ] Database backup taken (for major releases)

### 2. Run Migrations

**Important**: Run migrations in a separate step before deploying the new code.

```bash
# Docker
docker run --rm \
  -e DJANGO_SETTINGS_MODULE=gamification.settings \
  -e DB_HOST=... \
  -e DB_PASSWORD=... \
  $IMAGE_TAG python manage.py migrate --no-input

# Kubernetes
kubectl exec -n gamification deploy/gamification-api -- \
  python manage.py migrate --no-input
```

### 3. Deploy New Code

#### Docker Compose (Development)

```bash
# Pull latest image
docker compose pull

# Deploy with zero downtime
docker compose up -d --no-deps gamification-api gamification-grpc
```

#### Kubernetes (Production)

```bash
# Apply manifests
kubectl apply -k deployment/k8s/production/

# Or use a rolling update
kubectl set image deployment/gamification-api \
  gamification-api=$NEW_IMAGE_TAG \
  -n gamification

# Wait for rollout
kubectl rollout status deployment/gamification-api -n gamification
```

### 4. Verify Deployment

```bash
# Check health endpoints
curl http://service-url:8000/api/bonus/health/

# Check logs for errors
kubectl logs -n gamification -l app=gamification-api --tail=100

# Verify gRPC is responding
grpcurl -plaintext service-url:50051 list
```

### 5. Post-deployment

- [ ] Health checks pass
- [ ] No errors in logs
- [ ] Key functionality verified
- [ ] Update CHANGELOG.md with release notes
- [ ] Tag the release in Git

---

## Health Checks

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/bonus/health/` | Basic health check with DB connectivity |

### Expected Response

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-03T12:00:00Z"
}
```

### Kubernetes Probes

The deployment includes:

- **Liveness Probe**: Restarts container if unhealthy
- **Readiness Probe**: Removes from load balancer if not ready
- **Startup Probe**: Allows time for initial startup

---

## Rollback Procedures

### When to Rollback

- Health checks failing after deployment
- Significant increase in error rates
- Database migration failures
- Critical functionality broken

### Rollback Steps

#### 1. Rollback Code

```bash
# Kubernetes
kubectl rollout undo deployment/gamification-api -n gamification

# Or deploy previous image tag
kubectl set image deployment/gamification-api \
  gamification-api=$PREVIOUS_IMAGE_TAG \
  -n gamification

# Docker Compose
docker compose up -d --no-deps gamification-api gamification-grpc
```

#### 2. Rollback Migrations (if needed)

**Warning**: Only rollback migrations if absolutely necessary and the migration is reversible.

```bash
# List migrations
python manage.py showmigrations bonus

# Rollback to specific migration
python manage.py migrate bonus 0001_initial
```

#### 3. Restore Database (last resort)

If migration rollback is not possible:

```bash
# Restore from backup
pg_restore -h $DB_HOST -U $POSTGRES_USER -d gamification backup.dump
```

### Post-Rollback

1. Notify team of rollback
2. Investigate root cause
3. Create fix in a new branch
4. Re-test thoroughly before next deployment

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```
django.db.utils.OperationalError: could not connect to server
```

**Solution**: Check `DB_HOST`, `DB_PORT`, `DB_PASSWORD` environment variables. Verify network connectivity to database.

#### Migration Errors

```
django.db.utils.ProgrammingError: relation "..." already exists
```

**Solution**: Check if migrations are out of sync. May need to fake the migration:
```bash
python manage.py migrate --fake bonus 0001_initial
```

#### Kafka Connection Failed

```
KafkaException: Failed to connect to broker
```

**Solution**: Check `KAFKA_BOOTSTRAP_SERVERS`. Verify Kafka is reachable and credentials are correct.

#### gRPC Service Not Responding

**Solution**: Check gRPC server logs, verify port 50051 is exposed, check for registration errors.

### Logs

```bash
# View API logs
kubectl logs -n gamification -l app=gamification-api -f

# View gRPC logs
kubectl logs -n gamification -l app=gamification-grpc -f

# Search for errors
kubectl logs -n gamification -l app=gamification-api | grep -i error
```

### Contact

For deployment issues, contact:
- Team lead
- DevOps team
- On-call engineer

---

## Version History

| Version | Date | Deployer | Notes |
|---------|------|----------|-------|
| 0.1.0 | 2026-02-03 | - | Initial release |
