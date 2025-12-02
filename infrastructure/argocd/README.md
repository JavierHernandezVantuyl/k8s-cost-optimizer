# ArgoCD GitOps Configuration

ArgoCD configurations for continuous deployment of K8s Cost Optimizer using the app-of-apps pattern.

## Quick Start

### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Install Optimizer Project

```bash
kubectl apply -f projects/cost-optimizer.yaml
```

### 3. Deploy App-of-Apps

```bash
kubectl apply -f applications/root-app.yaml
```

This will automatically deploy all environments (dev, staging, prod).

## Architecture

```
root-app (app-of-apps)
├── dev-cost-optimizer (Kustomize)
├── staging-cost-optimizer (Helm)
└── prod-cost-optimizer (Kustomize)
```

## AppProject

The `cost-optimizer` AppProject defines:

- **Source repositories**: GitHub repos allowed
- **Destinations**: Clusters and namespaces
- **Resources**: Whitelisted Kubernetes resources
- **Roles**: RBAC for different user groups
- **Sync windows**: Automated deployment schedules

### Roles

- **admin**: Full access to all applications
- **developer**: Read-only + sync to dev
- **viewer**: Read-only access

## Applications

### Development (dev-app.yaml)

- **Source**: Kustomize overlay `infrastructure/kustomize/overlays/dev`
- **Destination**: `cost-optimizer-dev` namespace
- **Sync**: Automated with prune and self-heal
- **Wave**: 1 (deployed first)

### Staging (staging-app.yaml)

- **Source**: Helm chart with custom values
- **Destination**: `cost-optimizer-staging` namespace
- **Sync**: Automated
- **Wave**: 2 (deployed after dev)
- **Notifications**: Slack alerts on success

### Production (prod-app.yaml)

- **Source**: Kustomize overlay `infrastructure/kustomize/overlays/prod`
- **Destination**: `cost-optimizer` namespace
- **Sync**: Manual (no automated sync)
- **Wave**: 3 (deployed last)
- **Notifications**: Slack alerts on all events
- **Version**: Uses Git tags (e.g., `v1.0.0`)

## Sync Policies

### Automated Sync

```yaml
syncPolicy:
  automated:
    prune: true        # Delete resources not in Git
    selfHeal: true     # Re-sync on manual changes
    allowEmpty: false  # Don't delete everything
```

### Sync Options

- `CreateNamespace=true`: Auto-create namespaces
- `ApplyOutOfSyncOnly=true`: Only apply out-of-sync resources
- `PrunePropagationPolicy=foreground`: Wait for deletion

### Sync Waves

Applications are synced in order:
1. Wave 1: Development
2. Wave 2: Staging
3. Wave 3: Production

## Sync Windows

### Allowed Windows

- **Dev**: Monday-Friday, 8am-6pm (auto-sync, manual allowed)

### Denied Windows

- **Prod**: Daily, 12am-6am (no automated deploys during off-hours)

## Notifications

Configure Slack notifications:

```yaml
annotations:
  notifications.argoproj.io/subscribe.on-sync-succeeded.slack: cost-optimizer-alerts
  notifications.argoproj.io/subscribe.on-sync-failed.slack: cost-optimizer-alerts
```

## CLI Usage

### Login

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Login
argocd login argocd-server.argocd.svc.cluster.local
```

### Application Management

```bash
# List applications
argocd app list

# Get application details
argocd app get prod-cost-optimizer

# Sync application
argocd app sync prod-cost-optimizer

# Refresh (check Git for changes)
argocd app get prod-cost-optimizer --refresh

# Rollback
argocd app rollback prod-cost-optimizer

# Delete application
argocd app delete prod-cost-optimizer
```

### Diff

```bash
# Show diff between Git and cluster
argocd app diff prod-cost-optimizer

# Show manifests
argocd app manifests prod-cost-optimizer
```

## Health Checks

ArgoCD monitors application health:

- **Progressing**: Deployment in progress
- **Healthy**: All resources healthy
- **Degraded**: Some resources unhealthy
- **Suspended**: Manually suspended

### Ignore HPA Replicas

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
      - /spec/replicas
```

## Security

### Repository Access

Use SSH keys or HTTPS tokens:

```bash
argocd repo add https://github.com/your-org/k8s-cost-optimizer.git \
  --username git \
  --password $GITHUB_TOKEN
```

### RBAC

Map ArgoCD roles to SSO groups:

```yaml
roles:
  - name: admin
    groups:
      - cost-optimizer-admins
```

## Multi-Cluster

Deploy to multiple clusters:

```bash
# Add cluster
argocd cluster add eks-prod-cluster

# Deploy to specific cluster
argocd app create prod-optimizer \
  --dest-server https://eks-prod-cluster-url
```

## Troubleshooting

### Application stuck in "Progressing"

```bash
# Force refresh
argocd app get app-name --refresh --hard-refresh

# Check resource status
kubectl get all -n cost-optimizer
```

### Sync fails with "ComparisonError"

```bash
# Delete and re-create
argocd app delete app-name
kubectl apply -f applications/app-name.yaml
```

### Resource not being pruned

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-options: Prune=false  # Don't prune this resource
```

## Best Practices

1. **Use app-of-apps pattern**: Manage all apps from one root app
2. **Manual sync for production**: Require approval
3. **Sync waves**: Control deployment order
4. **Health checks**: Define custom health checks
5. **Notifications**: Alert on failures
6. **Git tags for prod**: Use immutable versions
7. **Ignore generated fields**: HPA replicas, status fields

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [App-of-Apps Pattern](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/)
- [Sync Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)
