# Deployment Guide

> Complete guide for deploying the Kubernetes Cost Optimizer in local, staging, and production environments

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Deployment](#production-deployment)
- [Configuration Reference](#configuration-reference)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security Hardening](#security-hardening)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Development Environment:**
- Docker Desktop 20.10+ with Kubernetes enabled
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space
- macOS, Linux, or Windows with WSL2

**Production Environment:**
- Kubernetes cluster 1.28+ (EKS, GKE, or AKS)
- PostgreSQL 15+ (managed service recommended)
- Redis 7+ (managed service recommended)
- Object storage (S3, GCS, or Azure Blob)
- Load balancer (ALB, Cloud Load Balancer, or Azure LB)

### Required Tools

```bash
# Check all prerequisites
docker --version          # 20.10+
docker-compose --version  # 2.0+
kubectl version --client  # 1.28+
helm version             # 3.12+
terraform version        # 1.5+
kind --version          # 0.20+ (for local multi-cluster)
python --version        # 3.11+
node --version          # 18+
make --version          # 4.0+
```

### Cloud Provider CLI Tools

**AWS:**
```bash
aws --version           # 2.13+
eksctl version         # 0.150+
```

**GCP:**
```bash
gcloud --version       # 400.0.0+
```

**Azure:**
```bash
az --version          # 2.50+
```

---

## Local Development Setup

### Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/k8s-cost-optimizer.git
cd k8s-cost-optimizer

# 2. Set up environment
cp .env.example .env

# 3. Start all services
make setup

# 4. Verify installation
make health-check
```

**Expected output:**
```
✓ PostgreSQL is ready
✓ Redis is ready
✓ MinIO is ready
✓ Prometheus is ready
✓ Grafana is ready
✓ AWS cluster is ready (3 nodes)
✓ GCP cluster is ready (2 nodes)
✓ Azure cluster is ready (2 nodes)

All systems operational! 🎉
```

### Detailed Setup Steps

#### 1. Environment Configuration

Edit `.env` file:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cost_optimizer
POSTGRES_USER=optimizer
POSTGRES_PASSWORD=changeme123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# MinIO (S3-compatible)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET=cost-reports

# API
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=info
API_WORKERS=4

# ML Engine
ML_MODEL_PATH=/app/models
ML_CONFIDENCE_THRESHOLD=0.8

# Cloud Provider Credentials (optional for demo)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

GOOGLE_APPLICATION_CREDENTIALS=
GCP_PROJECT_ID=

AZURE_SUBSCRIPTION_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
```

#### 2. Start Infrastructure

```bash
# Start databases and monitoring
make infra-start

# Verify databases
make db-check

# Initialize database schema
make db-migrate

# Seed demo data (optional)
make db-seed
```

#### 3. Start Application Services

**Backend API:**
```bash
cd services/optimizer-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for development

# Run migrations
alembic upgrade head

# Start API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Dashboard:**
```bash
cd services/dashboard
npm install

# Development server with hot reload
npm run dev

# Production build
npm run build
npm run preview
```

**Kubernetes Operator:**
```bash
cd services/operator

# Build operator
make build

# Deploy to local Kind cluster
make deploy

# View operator logs
make logs
```

#### 4. Create Multi-Cluster Environment

```bash
# Create 3 Kind clusters (simulates multi-cloud)
./scripts/setup-clusters.sh

# Verify clusters
kind get clusters
# Expected: aws-cluster, gcp-cluster, azure-cluster

# Check cluster status
kubectl cluster-info --context kind-aws-cluster
kubectl cluster-info --context kind-gcp-cluster
kubectl cluster-info --context kind-azure-cluster
```

#### 5. Deploy Sample Workloads

```bash
# Deploy demo workloads to all clusters
./demo/scripts/deploy-workloads.sh

# Verify deployments
kubectl get pods -A --context kind-aws-cluster
kubectl get pods -A --context kind-gcp-cluster
kubectl get pods -A --context kind-azure-cluster
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Dashboard** | http://localhost:3000 | - |
| **Grafana** | http://localhost:3001 | admin / admin123 |
| **Prometheus** | http://localhost:9090 | - |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |

---

## Docker Compose Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps

# Stop services
docker-compose down

# Clean everything (including volumes)
docker-compose down -v
```

### Production Environment

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=4

# Update a service
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api

# View resource usage
docker stats
```

### Custom Compose Configuration

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    ports:
      - "8000:8000"
    volumes:
      - ./services/optimizer-api:/app

  dashboard:
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./services/dashboard:/app
```

---

## Kubernetes Deployment

### Using Helm Charts

#### 1. Add Helm Repository

```bash
helm repo add cost-optimizer https://yourusername.github.io/k8s-cost-optimizer
helm repo update
```

#### 2. Install Chart

**Development:**
```bash
helm install cost-optimizer cost-optimizer/cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace \
  --values values-dev.yaml
```

**Staging:**
```bash
helm install cost-optimizer cost-optimizer/cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace \
  --values values-staging.yaml
```

**Production:**
```bash
helm install cost-optimizer cost-optimizer/cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace \
  --values values-prod.yaml
```

#### 3. Custom Values File

Create `values-custom.yaml`:

```yaml
# Application
replicaCount:
  api: 3
  operator: 2
  dashboard: 2

image:
  repository: ghcr.io/yourusername/k8s-cost-optimizer
  tag: "1.0.0"
  pullPolicy: IfNotPresent

# Resources
resources:
  api:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 4Gi

  operator:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi

# Autoscaling
autoscaling:
  api:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

# Database (external)
postgresql:
  enabled: false
  external:
    host: postgres.example.com
    port: 5432
    database: cost_optimizer
    username: optimizer
    existingSecret: postgres-credentials

# Redis (external)
redis:
  enabled: false
  external:
    host: redis.example.com
    port: 6379
    existingSecret: redis-credentials

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: cost-optimizer.example.com
      paths:
        - path: /
          pathType: Prefix
          service: dashboard
        - path: /api
          pathType: Prefix
          service: api
  tls:
    - secretName: cost-optimizer-tls
      hosts:
        - cost-optimizer.example.com

# Monitoring
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s

  grafana:
    enabled: true
    dashboards:
      enabled: true

# Security
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

podSecurityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

#### 4. Upgrade Deployment

```bash
# Upgrade to new version
helm upgrade cost-optimizer cost-optimizer/cost-optimizer \
  --namespace cost-optimizer \
  --values values-prod.yaml \
  --set image.tag=1.1.0

# Rollback if needed
helm rollback cost-optimizer 1 --namespace cost-optimizer

# View history
helm history cost-optimizer --namespace cost-optimizer
```

### Using Kustomize

#### 1. Base Configuration

```bash
cd infrastructure/kustomize/base
kubectl apply -k .
```

#### 2. Environment Overlays

**Development:**
```bash
kubectl apply -k infrastructure/kustomize/overlays/dev
```

**Staging:**
```bash
kubectl apply -k infrastructure/kustomize/overlays/staging
```

**Production:**
```bash
kubectl apply -k infrastructure/kustomize/overlays/prod
```

#### 3. Custom Overlay

Create `infrastructure/kustomize/overlays/custom/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: cost-optimizer

bases:
  - ../../base

patchesStrategicMerge:
  - deployment-patch.yaml
  - service-patch.yaml

configMapGenerator:
  - name: api-config
    literals:
      - LOG_LEVEL=info
      - WORKERS=4

secretGenerator:
  - name: api-secrets
    envs:
      - secrets.env

images:
  - name: optimizer-api
    newName: ghcr.io/yourusername/optimizer-api
    newTag: v1.0.0
```

### Using ArgoCD (GitOps)

#### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

#### 2. Create Application

```bash
kubectl apply -f infrastructure/argocd/applications/cost-optimizer.yaml
```

**Application manifest:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cost-optimizer
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/yourusername/k8s-cost-optimizer.git
    targetRevision: main
    path: infrastructure/kustomize/overlays/prod

  destination:
    server: https://kubernetes.default.svc
    namespace: cost-optimizer

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

#### 3. Monitor Deployment

```bash
# Via CLI
argocd app get cost-optimizer

# View sync status
argocd app sync cost-optimizer

# View application logs
argocd app logs cost-optimizer
```

---

## Production Deployment

### AWS EKS Deployment

#### 1. Provision Infrastructure with Terraform

```bash
cd infrastructure/terraform/environments/prod

# Initialize Terraform
terraform init

# Review plan
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan
```

**Key resources created:**
- EKS cluster with managed node groups
- RDS PostgreSQL instance (Multi-AZ)
- ElastiCache Redis cluster
- S3 bucket for reports
- VPC with public/private subnets
- Application Load Balancer
- IAM roles and policies
- CloudWatch log groups

#### 2. Configure kubectl

```bash
aws eks update-kubeconfig --name cost-optimizer-prod --region us-east-1
kubectl get nodes
```

#### 3. Install Add-ons

```bash
# Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=cost-optimizer-prod

# Cert Manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

#### 4. Deploy Application

```bash
# Using Helm
helm install cost-optimizer ./infrastructure/helm/cost-optimizer \
  -n cost-optimizer \
  --create-namespace \
  -f infrastructure/helm/cost-optimizer/values-eks.yaml

# Verify deployment
kubectl get all -n cost-optimizer
```

#### 5. Configure External DNS

```bash
# Deploy External DNS
kubectl apply -f infrastructure/kubernetes/external-dns-aws.yaml

# Verify DNS records
kubectl logs -n kube-system -l app=external-dns
```

### GCP GKE Deployment

#### 1. Create GKE Cluster

```bash
# Using gcloud
gcloud container clusters create cost-optimizer-prod \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-stackdriver-kubernetes

# Or using Terraform
cd infrastructure/terraform/environments/gcp-prod
terraform apply
```

#### 2. Configure kubectl

```bash
gcloud container clusters get-credentials cost-optimizer-prod \
  --region us-central1
```

#### 3. Deploy Application

```bash
helm install cost-optimizer ./infrastructure/helm/cost-optimizer \
  -n cost-optimizer \
  --create-namespace \
  -f infrastructure/helm/cost-optimizer/values-gke.yaml
```

### Azure AKS Deployment

#### 1. Create AKS Cluster

```bash
# Using Azure CLI
az aks create \
  --resource-group cost-optimizer-prod \
  --name cost-optimizer-prod \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10 \
  --enable-managed-identity \
  --enable-addons monitoring

# Or using Terraform
cd infrastructure/terraform/environments/azure-prod
terraform apply
```

#### 2. Configure kubectl

```bash
az aks get-credentials \
  --resource-group cost-optimizer-prod \
  --name cost-optimizer-prod
```

#### 3. Deploy Application

```bash
helm install cost-optimizer ./infrastructure/helm/cost-optimizer \
  -n cost-optimizer \
  --create-namespace \
  -f infrastructure/helm/cost-optimizer/values-aks.yaml
```

---

## Configuration Reference

### Environment Variables

#### API Service

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_HOST` | API bind address | `0.0.0.0` | No |
| `API_PORT` | API port | `8000` | No |
| `API_WORKERS` | Number of workers | `4` | No |
| `API_LOG_LEVEL` | Log level | `info` | No |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | Yes |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `POSTGRES_DB` | Database name | `cost_optimizer` | Yes |
| `POSTGRES_USER` | Database user | `optimizer` | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |
| `REDIS_HOST` | Redis host | `localhost` | Yes |
| `REDIS_PORT` | Redis port | `6379` | No |
| `REDIS_PASSWORD` | Redis password | - | No |
| `MINIO_ENDPOINT` | S3 endpoint | - | Yes |
| `MINIO_ACCESS_KEY` | S3 access key | - | Yes |
| `MINIO_SECRET_KEY` | S3 secret key | - | Yes |
| `ML_CONFIDENCE_THRESHOLD` | Min confidence | `0.8` | No |

#### Operator

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPERATOR_NAMESPACE` | Watch namespace | `all` | No |
| `RECONCILE_INTERVAL` | Reconcile period | `5m` | No |
| `API_ENDPOINT` | API endpoint | - | Yes |
| `DRY_RUN` | Dry run mode | `false` | No |

#### Dashboard

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | API URL | `http://localhost:8000` | Yes |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` | No |
| `VITE_REFRESH_INTERVAL` | Refresh interval (ms) | `30000` | No |

### ConfigMaps

**API Configuration:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  config.yaml: |
    api:
      host: 0.0.0.0
      port: 8000
      workers: 4
      log_level: info

    database:
      pool_size: 20
      max_overflow: 10
      pool_timeout: 30

    redis:
      pool_size: 10
      timeout: 5

    ml:
      confidence_threshold: 0.8
      lookback_days: 30
      min_data_points: 100

    recommendations:
      auto_apply: false
      dry_run_first: true
      approval_required: true
```

### Secrets

**Database Credentials:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
type: Opaque
stringData:
  username: optimizer
  password: changeme123
  host: postgres.example.com
  port: "5432"
  database: cost_optimizer
```

**Cloud Provider Credentials:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloud-credentials
type: Opaque
stringData:
  aws-access-key-id: AKIA...
  aws-secret-access-key: ...
  gcp-service-account.json: |
    {
      "type": "service_account",
      ...
    }
  azure-client-id: ...
  azure-client-secret: ...
  azure-tenant-id: ...
```

---

## Monitoring and Observability

### Prometheus Metrics

**API Metrics:**
- `api_requests_total` - Total HTTP requests
- `api_request_duration_seconds` - Request latency
- `api_errors_total` - Error count
- `recommendations_generated_total` - Recommendations created
- `recommendations_applied_total` - Applied recommendations
- `cost_savings_total` - Total cost savings

**Operator Metrics:**
- `operator_reconciliations_total` - Reconciliation count
- `operator_errors_total` - Operator errors
- `workloads_analyzed_total` - Analyzed workloads

### Grafana Dashboards

Import dashboards from `config/grafana/dashboards/`:

1. **Cost Optimizer Overview** - High-level metrics
2. **Recommendations** - Recommendation pipeline
3. **API Performance** - API latency and errors
4. **Database Performance** - PostgreSQL metrics
5. **Kubernetes Resources** - Cluster utilization

### Log Aggregation

**Using Loki:**
```bash
# Install Loki stack
helm install loki grafana/loki-stack \
  -n logging \
  --create-namespace \
  --set grafana.enabled=true \
  --set promtail.enabled=true
```

**Query examples:**
```logql
# API errors
{app="optimizer-api"} |= "ERROR"

# Slow requests
{app="optimizer-api"} | json | duration > 1s

# Recommendation generation
{app="optimizer-api"} |= "recommendation_generated"
```

### Alerting

**AlertManager Configuration:**
```yaml
route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#cost-optimizer-alerts'
        title: 'Cost Optimizer Alert'
```

**Sample Alerts:**
```yaml
groups:
  - name: cost-optimizer
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighRecommendationBacklog
        expr: recommendations_pending > 100
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "High recommendation backlog"
          description: "{{ $value }} pending recommendations"
```

---

## Security Hardening

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: optimizer-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: dashboard
      - podSelector:
          matchLabels:
            app: operator
      ports:
      - protocol: TCP
        port: 8000
  egress:
    - to:
      - podSelector:
          matchLabels:
            app: postgres
      ports:
      - protocol: TCP
        port: 5432
    - to:
      - podSelector:
          matchLabels:
            app: redis
      ports:
      - protocol: TCP
        port: 6379
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cost-optimizer
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: optimizer-operator
  namespace: cost-optimizer
rules:
  - apiGroups: ["optimizer.k8s.io"]
    resources: ["optimizationrecommendations"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
```

### Secrets Management

**Using Sealed Secrets:**
```bash
# Install sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  -n kube-system

# Create sealed secret
kubectl create secret generic db-credentials \
  --from-literal=password=changeme123 \
  --dry-run=client -o yaml | \
kubeseal -o yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

**Using External Secrets Operator:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: postgres-credentials
  data:
    - secretKey: password
      remoteRef:
        key: prod/cost-optimizer/postgres
        property: password
```

---

## Backup and Recovery

### Database Backups

**Automated PostgreSQL Backups:**
```bash
# Create backup
kubectl exec -n cost-optimizer postgres-0 -- \
  pg_dump -U optimizer cost_optimizer | \
  gzip > backup-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql.gz \
  s3://cost-optimizer-backups/postgres/
```

**CronJob for automated backups:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U optimizer cost_optimizer | \
              gzip | \
              aws s3 cp - s3://cost-optimizer-backups/postgres/backup-$(date +%Y%m%d).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
          restartPolicy: OnFailure
```

### Disaster Recovery

**Recovery Procedure:**
```bash
# 1. Download latest backup
aws s3 cp s3://cost-optimizer-backups/postgres/backup-latest.sql.gz .

# 2. Restore database
gunzip < backup-latest.sql.gz | \
kubectl exec -i -n cost-optimizer postgres-0 -- \
  psql -U optimizer cost_optimizer

# 3. Verify data
kubectl exec -n cost-optimizer postgres-0 -- \
  psql -U optimizer cost_optimizer -c "SELECT COUNT(*) FROM recommendations;"

# 4. Restart services
kubectl rollout restart deployment/optimizer-api -n cost-optimizer
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Symptom:** Containers crash or restart loop

**Diagnosis:**
```bash
# Check container logs
docker-compose logs api
kubectl logs -n cost-optimizer deployment/optimizer-api

# Check events
kubectl get events -n cost-optimizer --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n cost-optimizer
```

**Solutions:**
- Increase memory limits if OOMKilled
- Check database connectivity
- Verify environment variables
- Review configuration files

#### 2. Database Connection Errors

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Diagnosis:**
```bash
# Test PostgreSQL connectivity
kubectl exec -it -n cost-optimizer postgres-0 -- psql -U optimizer -d cost_optimizer

# Check PostgreSQL logs
kubectl logs -n cost-optimizer postgres-0

# Verify service
kubectl get svc -n cost-optimizer postgres
```

**Solutions:**
- Verify credentials in secrets
- Check network policies
- Ensure PostgreSQL is ready
- Check connection pooling settings

#### 3. High API Latency

**Symptom:** Requests taking >2 seconds

**Diagnosis:**
```bash
# Check API metrics
curl http://localhost:8000/metrics

# Check database query performance
kubectl exec -it -n cost-optimizer postgres-0 -- \
  psql -U optimizer cost_optimizer -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis latency
redis-cli --latency
```

**Solutions:**
- Add database indexes
- Increase API workers
- Enable Redis caching
- Optimize queries
- Scale horizontally

#### 4. Recommendations Not Generating

**Symptom:** No recommendations appear in dashboard

**Diagnosis:**
```bash
# Check analysis jobs
kubectl get pods -n cost-optimizer -l job=analysis

# Check ML engine logs
kubectl logs -n cost-optimizer -l app=ml-engine

# Verify metrics collection
kubectl exec -n cost-optimizer metrics-server-0 -- \
  curl http://localhost:8080/metrics
```

**Solutions:**
- Ensure metrics are being collected
- Check confidence threshold settings
- Verify workload has sufficient history (30 days)
- Check ML model availability

#### 5. Operator Not Applying Recommendations

**Symptom:** Recommendations stuck in "Pending" status

**Diagnosis:**
```bash
# Check operator logs
kubectl logs -n cost-optimizer -l app=optimizer-operator

# Check RBAC permissions
kubectl auth can-i update deployments --as=system:serviceaccount:cost-optimizer:operator

# Check CRD status
kubectl get optimizationrecommendations -A
```

**Solutions:**
- Verify RBAC permissions
- Enable dry-run mode for testing
- Check approval workflow settings
- Review operator configuration

#### 6. Cluster Creation Fails (Local Development)

**Symptom:** Kind cluster creation times out

**Diagnosis:**
```bash
# Check Kind logs
kind export logs /tmp/kind-logs

# Check Docker resources
docker system df
docker info
```

**Solutions:**
```bash
# Increase Docker resources (Docker Desktop)
# - CPU: 4+ cores
# - Memory: 8GB+
# - Disk: 50GB+

# Clean up old clusters
kind delete cluster --name aws-cluster
kind delete cluster --name gcp-cluster
kind delete cluster --name azure-cluster

# Recreate clusters
./scripts/setup-clusters.sh
```

#### 7. Demo Not Showing Expected Savings

**Symptom:** Demo shows <35% savings

**Diagnosis:**
```bash
# Check demo data
kubectl exec -it -n cost-optimizer postgres-0 -- \
  psql -U optimizer cost_optimizer -c \
  "SELECT SUM(monthly_savings) FROM recommendations WHERE confidence > 0.8;"

# Verify workload data
./demo/scripts/validate-data.sh
```

**Solutions:**
```bash
# Regenerate demo data
./demo/scripts/generate-data.sh --scenario=impressive

# Reset and rerun demo
make clean-data
make demo
```

### Performance Tuning

#### API Optimization

```yaml
# Increase workers and resources
apiVersion: apps/v1
kind: Deployment
metadata:
  name: optimizer-api
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: api
        env:
        - name: API_WORKERS
          value: "8"
        - name: DB_POOL_SIZE
          value: "20"
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 8Gi
```

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_recommendations_confidence ON recommendations(confidence DESC);
CREATE INDEX idx_recommendations_created ON recommendations(created_at DESC);
CREATE INDEX idx_analyses_cluster ON analyses(cluster_id, created_at DESC);

-- Tune PostgreSQL parameters
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET max_connections = 200;
```

#### Redis Optimization

```bash
# Increase memory
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Enable persistence
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### Debug Mode

Enable debug logging:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  LOG_LEVEL: debug
  DEBUG: "true"
  SQL_ECHO: "true"
```

### Getting Help

1. **Check documentation:**
   - [README.md](../README.md)
   - [ARCHITECTURE.md](../ARCHITECTURE.md)
   - [API Documentation](http://localhost:8000/docs)

2. **View logs:**
   ```bash
   make logs
   kubectl logs -n cost-optimizer -l app=optimizer-api --tail=100
   ```

3. **Health checks:**
   ```bash
   make health-check
   curl http://localhost:8000/health
   ```

4. **Community support:**
   - [GitHub Issues](https://github.com/yourusername/k8s-cost-optimizer/issues)
   - [GitHub Discussions](https://github.com/yourusername/k8s-cost-optimizer/discussions)

---

## Next Steps

After successful deployment:

1. **Run the demo:** `make demo`
2. **Generate report:** `make demo-report`
3. **Set up monitoring:** Configure Grafana dashboards
4. **Enable alerting:** Configure AlertManager
5. **Review security:** Complete security checklist
6. **Load testing:** Run performance tests
7. **Backup testing:** Verify backup/restore procedures

---

**Need help?** Open an issue on [GitHub](https://github.com/yourusername/k8s-cost-optimizer/issues)
