# K8s Cost Optimizer - Infrastructure as Code

This directory contains production-ready Infrastructure as Code (IaC) for deploying the K8s Cost Optimizer platform to any cloud provider.

## Directory Structure

```
infrastructure/
├── terraform/          # Terraform modules for cloud infrastructure
├── helm/              # Helm charts for Kubernetes deployment
├── kustomize/         # Kustomize overlays for environments
├── argocd/            # ArgoCD GitOps configurations
├── ansible/           # Ansible playbooks for automation
├── crossplane/        # Crossplane compositions for cloud resources
└── README.md          # This file
```

## Quick Start

### Prerequisites

- **Terraform** >= 1.5.0
- **Helm** >= 3.13.0
- **kubectl** >= 1.28.0
- **kustomize** >= 5.0.0
- **ArgoCD CLI** (optional)
- **Ansible** >= 2.15 (optional)
- **Crossplane** >= 1.14 (optional)

### Deployment Options

#### Option 1: Terraform + Helm (Recommended for getting started)

```bash
# 1. Create cloud infrastructure
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# 2. Deploy optimizer using Helm
helm install cost-optimizer ../../helm/cost-optimizer \
  --namespace cost-optimizer \
  --create-namespace \
  -f values-dev.yaml
```

#### Option 2: Kustomize (Recommended for Kubernetes-native)

```bash
# Deploy to dev
kubectl apply -k kustomize/overlays/dev

# Deploy to prod
kubectl apply -k kustomize/overlays/prod
```

#### Option 3: ArgoCD (Recommended for GitOps)

```bash
# Install ArgoCD project
kubectl apply -f argocd/projects/cost-optimizer.yaml

# Install app-of-apps
kubectl apply -f argocd/applications/root-app.yaml
```

#### Option 4: Ansible (Recommended for automation)

```bash
# Deploy to dev environment
cd ansible
ansible-playbook playbooks/deploy-optimizer.yml -e target_env=dev
```

#### Option 5: Crossplane (Recommended for cloud-native)

```bash
# Install providers
kubectl apply -f crossplane/providers/

# Create resources
kubectl apply -f crossplane/claims/dev-database.yaml
kubectl apply -f crossplane/claims/dev-redis.yaml
kubectl apply -f crossplane/claims/dev-storage.yaml
```

## Infrastructure Components

### Cloud Providers Supported

- **AWS**: EKS, RDS PostgreSQL, ElastiCache Redis, S3
- **GCP**: GKE, Cloud SQL, Memorystore, Cloud Storage
- **Azure**: AKS, PostgreSQL Flexible Server, Azure Cache for Redis, Blob Storage

### Deployment Methods

| Method | Use Case | Complexity | GitOps | Cloud-Native |
|--------|----------|------------|--------|--------------|
| **Terraform** | Full stack deployment | Medium | No | Yes |
| **Helm** | Kubernetes app deployment | Low | No | Yes |
| **Kustomize** | Environment-specific configs | Low | Yes | Yes |
| **ArgoCD** | Continuous deployment | Medium | Yes | Yes |
| **Ansible** | Automation & orchestration | Medium | No | No |
| **Crossplane** | Cloud resource management | High | Yes | Yes |

## Environment Configuration

### Development

- **Namespace**: `cost-optimizer-dev`
- **Replicas**: 1 API, 1 Dashboard
- **Resources**: Minimal (100m CPU, 256Mi memory)
- **Auto-scaling**: Disabled
- **Dry-run**: Enabled

### Staging

- **Namespace**: `cost-optimizer-staging`
- **Replicas**: 2 API, 2 Dashboard
- **Resources**: Medium (250m CPU, 512Mi memory)
- **Auto-scaling**: Enabled (2-5 replicas)
- **Dry-run**: Enabled

### Production

- **Namespace**: `cost-optimizer`
- **Replicas**: 3 API, 3 Dashboard
- **Resources**: High (500m CPU, 1Gi memory)
- **Auto-scaling**: Enabled (3-20 replicas)
- **Dry-run**: Disabled
- **High Availability**: Yes

## Cost Tagging Strategy

All resources are tagged with:

- `Environment`: dev | staging | prod
- `CostCenter`: infrastructure | development
- `ManagedBy`: terraform | helm | crossplane
- `Application`: cost-optimizer
- `Project`: k8s-cost-optimizer

## Security Considerations

### Secrets Management

- **Development**: Kubernetes secrets (not recommended for production)
- **Production**: External Secrets Operator or cloud-native secret managers
  - AWS: Secrets Manager or Parameter Store
  - GCP: Secret Manager
  - Azure: Key Vault

### Network Policies

- Enabled in production
- API pods can only communicate with dashboard pods
- Egress restricted to necessary services

### Pod Security

- Security contexts enforced
- Run as non-root user
- Read-only root filesystem
- Capabilities dropped

## CI/CD Integration

GitHub Actions workflows are provided for:

- **Terraform Plan/Apply**: `.github/workflows/terraform-plan.yml`
- **Docker Build/Push**: `.github/workflows/docker-build.yml`
- **Helm Testing**: `.github/workflows/helm-test.yml`
- **Security Scanning**: `.github/workflows/security-scan.yml`

## Disaster Recovery

### Backup Strategy

- **Database**: Automated backups (7 days dev, 30 days prod)
- **Redis**: Daily snapshots
- **Storage**: Versioning enabled

### Restore Procedure

```bash
# Terraform state
terraform state pull > backup.tfstate

# Helm releases
helm list -A > releases.txt

# Kubernetes resources
kubectl get all -n cost-optimizer -o yaml > backup.yaml
```

## Monitoring & Observability

### Metrics

- Prometheus metrics exposed on `:9090/metrics`
- ServiceMonitor for automatic discovery

### Logging

- Structured JSON logs
- Cloud-native logging (CloudWatch, Stackdriver, Azure Monitor)

### Dashboards

- Grafana dashboards in `config/grafana/`
- Pre-configured for cost optimization metrics

## Troubleshooting

### Common Issues

1. **Helm install fails with "namespace not found"**
   ```bash
   kubectl create namespace cost-optimizer
   ```

2. **Pods stuck in ImagePullBackOff**
   ```bash
   # Check image pull secrets
   kubectl get secrets -n cost-optimizer
   kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...
   ```

3. **Database connection errors**
   ```bash
   # Verify secrets
   kubectl get secret postgres-credentials -n cost-optimizer -o yaml
   ```

4. **ArgoCD sync fails**
   ```bash
   # Check application status
   argocd app get cost-optimizer
   argocd app sync cost-optimizer --prune
   ```

## Contributing

When adding new infrastructure:

1. Update the appropriate IaC method (Terraform/Helm/etc.)
2. Test in dev environment first
3. Update documentation
4. Add cost tags
5. Run security scans
6. Create PR with changes

## Support

For issues or questions:

- Check documentation in each subdirectory
- Review GitHub Actions workflow runs
- Consult cloud provider documentation

## License

Part of the K8s Cost Optimizer platform.
