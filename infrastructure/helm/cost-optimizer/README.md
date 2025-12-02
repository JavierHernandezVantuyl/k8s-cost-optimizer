# Cost Optimizer Helm Chart

Official Helm chart for deploying K8s Cost Optimizer to any Kubernetes cluster.

## TL;DR

```bash
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace
```

## Prerequisites

- Kubernetes 1.28+
- Helm 3.13+
- PostgreSQL database (external or managed)
- Redis cache (external or managed)
- S3-compatible storage (external or managed)

## Installing the Chart

```bash
# With default values
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace

# With custom values
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  -f values-prod.yaml \
  --set api.image.tag=v1.0.0

# With secrets from files
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  --set-file database.password=./secrets/db-password.txt
```

## Uninstalling the Chart

```bash
helm uninstall cost-optimizer --namespace cost-optimizer
```

## Configuration

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |
| `global.costCenter` | Cost center for billing | `infrastructure` |
| `namespace` | Kubernetes namespace | `cost-optimizer` |

### API Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.enabled` | Enable API deployment | `true` |
| `api.replicaCount` | Number of API replicas | `2` |
| `api.image.repository` | API image repository | `your-registry/k8s-cost-optimizer-api` |
| `api.image.tag` | API image tag | `1.0.0` |
| `api.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `api.resources.requests.cpu` | CPU requests | `250m` |
| `api.resources.requests.memory` | Memory requests | `512Mi` |
| `api.resources.limits.cpu` | CPU limits | `1000m` |
| `api.resources.limits.memory` | Memory limits | `2Gi` |
| `api.autoscaling.enabled` | Enable HPA | `true` |
| `api.autoscaling.minReplicas` | Minimum replicas | `2` |
| `api.autoscaling.maxReplicas` | Maximum replicas | `10` |

### Dashboard Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dashboard.enabled` | Enable dashboard deployment | `true` |
| `dashboard.replicaCount` | Number of dashboard replicas | `2` |
| `dashboard.image.repository` | Dashboard image repository | `your-registry/k8s-cost-optimizer-dashboard` |
| `dashboard.image.tag` | Dashboard image tag | `1.0.0` |

### Database Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `database.host` | PostgreSQL host | `""` |
| `database.port` | PostgreSQL port | `5432` |
| `database.name` | Database name | `k8s_optimizer` |
| `database.username` | Database username | `optimizer` |
| `database.existingSecret` | Name of existing secret | `postgres-credentials` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.host` | Redis host | `""` |
| `redis.port` | Redis port | `6379` |
| `redis.existingSecret` | Name of existing secret | `redis-credentials` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `optimizer.example.com` |
| `ingress.tls[0].secretName` | TLS secret name | `optimizer-tls` |

### RBAC Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rbac.create` | Create RBAC resources | `true` |
| `rbac.role.enabled` | Create Role for write permissions | `false` |

## Examples

### Production Deployment

```bash
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace \
  -f values-prod.yaml \
  --set api.image.tag=v1.0.0 \
  --set dashboard.image.tag=v1.0.0 \
  --set database.host=postgres.example.com \
  --set redis.host=redis.example.com \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=optimizer.production.example.com
```

### Development Deployment

```bash
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer-dev \
  --create-namespace \
  --set global.environment=dev \
  --set api.replicaCount=1 \
  --set dashboard.replicaCount=1 \
  --set api.autoscaling.enabled=false \
  --set rbac.role.enabled=false
```

### With External Secrets

Using External Secrets Operator:

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
  namespace: cost-optimizer
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: postgres-credentials
  data:
    - secretKey: host
      remoteRef:
        key: optimizer/postgres
        property: host
    - secretKey: password
      remoteRef:
        key: optimizer/postgres
        property: password
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  -f values-prod.yaml \
  --set api.image.tag=v1.1.0

# Rollback
helm rollback cost-optimizer --namespace cost-optimizer
```

## Testing

```bash
# Template and validate
helm template cost-optimizer ./cost-optimizer --debug

# Dry run install
helm install cost-optimizer ./cost-optimizer \
  --namespace cost-optimizer \
  --dry-run --debug

# Run tests
helm test cost-optimizer --namespace cost-optimizer
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pods -n cost-optimizer
kubectl logs -n cost-optimizer -l app.kubernetes.io/name=cost-optimizer
```

### Database connection errors

```bash
# Verify secrets
kubectl get secret postgres-credentials -n cost-optimizer -o yaml

# Test connection
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

### Ingress not working

```bash
# Check ingress
kubectl describe ingress -n cost-optimizer

# Check ingress controller
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

## Values Files

- `values.yaml`: Default values
- `values-prod.yaml`: Production configuration with high availability

## Architecture

```
┌─────────────────┐
│   Ingress       │
│  (nginx)        │
└────────┬────────┘
         │
    ┌────┴──────┐
    │           │
┌───▼──┐   ┌───▼────┐
│ API  │   │Dashboard│
│ (3x) │   │  (3x)   │
└───┬──┘   └─────────┘
    │
    ├──► PostgreSQL
    ├──► Redis
    └──► S3/MinIO
```

## Security

- All pods run as non-root
- Read-only root filesystem
- Dropped capabilities
- Network policies (optional)
- Pod security policies (optional)

## Monitoring

Prometheus metrics exposed at `/metrics`:
- `optimizer_recommendations_total`
- `optimizer_savings_monthly`
- `optimizer_workloads_analyzed`

## License

Part of the K8s Cost Optimizer platform.
