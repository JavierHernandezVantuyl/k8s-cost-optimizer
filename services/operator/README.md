# K8s Cost Optimizer Operator

Kubernetes operator for automatic cost optimization using the kopf framework. Watches workloads and applies ML-driven optimizations to reduce infrastructure costs by 35-40%.

## Architecture

```
operator/
├── main.py                         # Kopf operator with CRD handlers
├── handlers/
│   ├── optimization_handler.py     # Apply optimizations to workloads
│   ├── workload_handler.py        # Watch and validate workloads
│   └── rollback_handler.py        # Automatic rollback functionality
├── webhooks/
│   └── admission_webhook.py       # Validate CostOptimization resources
├── crds/
│   └── costoptimization-crd.yaml  # Custom Resource Definition
├── manifests/
│   ├── operator/                   # Operator deployment manifests
│   └── examples/                   # Example CostOptimization resources
└── Dockerfile                      # Multi-stage container build
```

## Custom Resource Definition (CRD)

### CostOptimization Resource

```yaml
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: optimize-frontend-cpu
  namespace: default
spec:
  targetWorkload:
    name: frontend-web
    kind: Deployment          # Deployment, StatefulSet, DaemonSet
    namespace: default
  optimizationType: CPU       # CPU, MEMORY, REPLICAS, ALL, SPOT_INSTANCES, SCHEDULED_SCALING
  maxChangePercent: 50        # Maximum allowed change (1-100)
  minConfidence: 0.75         # Minimum ML confidence (0.0-1.0)
  dryRun: true                # Show what would change without applying
  autoApply: false            # Automatically apply when optimization found
  rollbackOnFailure: true     # Auto-rollback on failure
  maxRiskLevel: MEDIUM        # LOW, MEDIUM, HIGH, CRITICAL
  metricsWindow: 7d           # Time window for analysis (1h, 24h, 7d, 30d)
  schedule: "0 */6 * * *"     # Cron schedule for periodic checks
```

### Status Fields

```yaml
status:
  phase: Applied                    # Pending, Analyzing, Ready, Applying, Applied, Failed, RolledBack
  message: "Optimization applied successfully"
  lastAnalysis: "2024-01-15T10:30:00Z"
  lastApplied: "2024-01-15T10:35:00Z"
  currentRecommendation:
    optimizationType: right_size_cpu
    currentCost: 876.00
    optimizedCost: 438.00
    monthlySavings: 438.00
    confidenceScore: 0.92
    riskLevel: LOW
    changes:
      cpu_request: "750m"
      memory_request: "2Gi"
  appliedOptimizations: 3
  totalSavings: 1250.00
  conditions: [...]
```

## Operator Functionality

### 1. CRD Handlers (main.py)

#### `@kopf.on.create`
Triggered when a new CostOptimization resource is created:
- Validates target workload exists
- Sets initial status to `Analyzing`
- Logs event to Kubernetes events

#### `@kopf.on.update`
Triggered when CostOptimization resource is updated:
- Detects configuration changes
- Re-analyzes if optimization parameters changed
- Updates status accordingly

#### `@kopf.on.delete`
Triggered when CostOptimization resource is deleted:
- Executes rollback if optimization was applied
- Cleans up rollback state from Redis/ConfigMap
- Logs deletion event

#### `@kopf.timer` (Every 30 minutes)
Periodic optimization checks:
- Fetches latest metrics from optimizer API
- Generates ML-based recommendations
- Auto-applies if conditions met:
  - `autoApply: true`
  - `dryRun: false`
  - Confidence >= `minConfidence`
  - Risk level <= `maxRiskLevel`
- Updates status with current recommendation
- Increments Prometheus metrics

### 2. Optimization Handler

#### `analyze_workload()`
- Fetches workload from Kubernetes
- Calls optimizer API for ML recommendations
- Returns best recommendation by savings

#### `apply_optimization()`
- Stores original state for rollback
- Applies recommended configuration:
  - **CPU/Memory**: Updates resource requests/limits
  - **Replicas**: Scales deployment/statefulset
  - **Spot Instances**: Updates node affinity
- Adds annotations to track optimization
- Returns success/failure

#### Supported Workload Types
- **Deployment**: Full support for all optimization types
- **StatefulSet**: Requires manual approval for replica reduction
- **DaemonSet**: CPU/Memory only (no replica changes)

### 3. Workload Handler

#### `watch_deployments()` / `watch_statefulsets()`
- Lists all workloads in cluster
- Extracts current resource configuration
- Returns workload metadata

#### `calculate_usage()`
- Fetches metrics from optimizer API
- Returns CPU/memory utilization statistics
- Used for validation before applying

#### `validate_optimization()`
Safety checks before applying optimization:
- **Change Threshold**: Ensures change <= `maxChangePercent`
- **Minimum Replicas**: Never reduces below 1
- **StatefulSet Protection**: Blocks auto-reduce for StatefulSets
- **PodDisruptionBudget**: Respects PDB constraints
- **Resource Limits**: Validates CPU/memory changes

### 4. Rollback Handler

#### `store_original_state()`
Backup strategies (redundant for safety):
- **Redis**: 7-day TTL for fast access
- **ConfigMap**: Persistent backup in cluster

Stores:
- Original replica count
- Original resource requests/limits
- Annotations and labels
- Timestamp of change

#### `execute_rollback()`
- Retrieves original state from Redis or ConfigMap
- Restores previous configuration:
  - Replica count
  - CPU/memory requests
  - CPU/memory limits
- Adds rollback annotations
- Validates successful restoration

#### `validate_rollback()`
Post-rollback verification:
- Checks replica count matches original
- Verifies resource requests/limits
- Logs validation results

### 5. Admission Webhook

#### Validation Rules

**Required Fields:**
- `targetWorkload.name`
- `targetWorkload.kind`
- `optimizationType`

**Value Constraints:**
- `maxChangePercent`: 1-100
- `minConfidence`: 0.0-1.0
- `maxRiskLevel`: LOW, MEDIUM, HIGH, CRITICAL

**Safety Rules:**
- Cannot enable both `autoApply` and `dryRun`
- Cannot auto-apply with `maxRiskLevel` HIGH or CRITICAL
- StatefulSet replica optimization requires manual intervention
- DaemonSet cannot have replica optimization

**Protected Resources:**
- Namespaces: `kube-system`, `kube-public`, `kube-node-lease`
- Workloads: `kube-dns`, `coredns`, `kube-proxy`, `metrics-server`
- Controllers: Any workload with `app.kubernetes.io/component=controller`

**Risk Limits:**
- Cannot auto-apply with `maxChangePercent` > 80%
- Spot instances require `minConfidence` >= 0.8 for auto-apply

#### Mutation Rules

Automatic mutations applied:
- Sets initial `status.phase` to `Pending`
- Adds `app.kubernetes.io/managed-by: cost-optimizer-operator` label
- Initializes status counters (`appliedOptimizations: 0`, `totalSavings: 0.0`)

## Prometheus Metrics

The operator exposes metrics on port 8080:

```
# Total CostOptimization resources created
costopt_optimizations_created_total

# Total optimizations applied by type
costopt_optimizations_applied_total{optimization_type="right_size_cpu"}

# Total failed optimizations by reason
costopt_optimizations_failed_total{reason="application_failed"}

# Total rollbacks executed
costopt_rollbacks_total

# Total monthly savings in USD
costopt_total_monthly_savings_usd

# Optimization duration in seconds
costopt_optimization_duration_seconds (histogram)
```

## Deployment

### Prerequisites

1. **Install CRD:**
```bash
kubectl apply -f services/operator/crds/costoptimization-crd.yaml
```

2. **Create Namespace and RBAC:**
```bash
kubectl apply -f services/operator/manifests/operator/operator-rbac.yaml
```

3. **Deploy Operator:**
```bash
# Build Docker image
docker build -t cost-optimizer-operator:latest services/operator/

# Load into Kind clusters
kind load docker-image cost-optimizer-operator:latest --name aws-cluster
kind load docker-image cost-optimizer-operator:latest --name gcp-cluster
kind load docker-image cost-optimizer-operator:latest --name azure-cluster

# Deploy operator
kubectl apply -f services/operator/manifests/operator/operator-deployment.yaml
```

### Verify Installation

```bash
# Check operator is running
kubectl get pods -n cost-optimizer

# Check CRD is installed
kubectl get crd costoptimizations.optimization.k8s.io

# View operator logs
kubectl logs -n cost-optimizer -l app=cost-optimizer-operator -f

# Check Prometheus metrics
kubectl port-forward -n cost-optimizer svc/cost-optimizer-operator 8080:8080
curl http://localhost:8080/metrics
```

## Usage Examples

### Example 1: Dry-Run CPU Optimization

Analyze without applying changes:

```bash
kubectl apply -f services/operator/manifests/examples/cpu-optimization.yaml
```

```yaml
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: optimize-frontend-cpu
spec:
  targetWorkload:
    name: frontend-web
    kind: Deployment
  optimizationType: CPU
  dryRun: true
  autoApply: false
```

View recommendations:

```bash
kubectl get costopt optimize-frontend-cpu -o yaml

# Check status
kubectl describe costopt optimize-frontend-cpu
```

### Example 2: Auto-Apply Replica Optimization

Automatically optimize replicas every 12 hours:

```bash
kubectl apply -f services/operator/manifests/examples/replica-optimization.yaml
```

```yaml
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: optimize-api-replicas
spec:
  targetWorkload:
    name: api-gateway
    kind: Deployment
  optimizationType: REPLICAS
  minConfidence: 0.80
  dryRun: false
  autoApply: true
  maxRiskLevel: LOW
  schedule: "0 */12 * * *"
```

Monitor progress:

```bash
# Watch status changes
kubectl get costopt optimize-api-replicas -w

# View events
kubectl get events --field-selector involvedObject.name=optimize-api-replicas
```

### Example 3: Comprehensive Optimization

Apply all optimization types weekly:

```bash
kubectl apply -f services/operator/manifests/examples/full-optimization.yaml
```

```yaml
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: optimize-microservice-all
  namespace: production
spec:
  targetWorkload:
    name: microservice-analytics
    kind: Deployment
  optimizationType: ALL
  maxChangePercent: 30
  minConfidence: 0.85
  autoApply: true
  maxRiskLevel: MEDIUM
  schedule: "0 0 * * 0"  # Weekly on Sunday
```

### Example 4: Manual Rollback

Trigger manual rollback by deleting the resource:

```bash
# Delete CostOptimization (triggers automatic rollback if rollbackOnFailure: true)
kubectl delete costopt optimize-frontend-cpu

# Verify rollback in logs
kubectl logs -n cost-optimizer -l app=cost-optimizer-operator
```

## Workflow

### Typical Flow for Auto-Apply

1. **Create CostOptimization resource**
   - Operator receives create event
   - Sets status to `Analyzing`
   - Validates target workload exists

2. **Initial Analysis**
   - Fetches workload metrics (7-30 days)
   - Calls optimizer API for ML recommendation
   - Updates status with recommendation

3. **Periodic Checks (Every 30 min)**
   - Re-analyzes workload
   - Checks if optimization criteria met:
     - Confidence >= `minConfidence`
     - Risk <= `maxRiskLevel`
     - Change <= `maxChangePercent`

4. **Auto-Apply (If enabled)**
   - Stores original state to Redis + ConfigMap
   - Applies recommended changes
   - Updates status to `Applied`
   - Increments Prometheus metrics
   - Creates Kubernetes event

5. **Monitoring**
   - Continues periodic checks
   - Updates recommendations as metrics change
   - Can re-optimize if new opportunities found

6. **Rollback (On delete or failure)**
   - Retrieves original state
   - Restores previous configuration
   - Validates successful restoration

## Configuration

### Environment Variables

```bash
OPTIMIZER_API_URL        # URL to optimizer API (default: http://optimizer-api:8000)
REDIS_HOST               # Redis host for rollback state (default: redis)
REDIS_PORT               # Redis port (default: 6379)
PROMETHEUS_PORT          # Metrics port (default: 8080)
KOPF_LOG_LEVEL          # Logging level (default: INFO)
```

### Operator Settings

In `main.py`:

```python
settings.posting.level = logging.INFO              # Event logging level
settings.watching.connect_timeout = 1 * 60         # API connection timeout
settings.watching.server_timeout = 10 * 60         # Watch timeout
```

## Safety Features

### Built-in Protections

1. **Dry-Run Mode**: Default mode shows changes without applying
2. **Validation Webhook**: Blocks dangerous configurations
3. **Change Limits**: `maxChangePercent` prevents drastic changes
4. **Confidence Threshold**: `minConfidence` ensures ML accuracy
5. **Risk Assessment**: `maxRiskLevel` blocks high-risk optimizations
6. **Rollback**: Automatic restoration on failure or deletion
7. **PodDisruptionBudget**: Respects availability requirements
8. **Protected Namespaces**: Blocks system namespace modifications

### Testing Optimizations

1. **Start with Dry-Run:**
```yaml
dryRun: true
autoApply: false
```

2. **Review Recommendations:**
```bash
kubectl describe costopt <name>
```

3. **Enable Auto-Apply Gradually:**
```yaml
dryRun: false
autoApply: true
maxChangePercent: 20      # Start conservative
minConfidence: 0.90       # High confidence only
maxRiskLevel: LOW         # Low risk only
```

4. **Monitor Results:**
```bash
# Check metrics
curl http://localhost:8080/metrics | grep costopt

# Watch events
kubectl get events -w

# Check workload health
kubectl get pods -w
```

## Troubleshooting

### Operator Not Starting

```bash
# Check logs
kubectl logs -n cost-optimizer -l app=cost-optimizer-operator

# Common issues:
# - CRD not installed
# - RBAC permissions missing
# - Optimizer API unreachable
```

### Optimization Not Applying

```bash
# Check CostOptimization status
kubectl describe costopt <name>

# Common reasons:
# - dryRun: true
# - Confidence below threshold
# - Risk level too high
# - Change percent exceeds limit
# - Validation webhook blocking
```

### Rollback Failed

```bash
# Check if rollback state exists
kubectl get configmap <workload-name>-rollback-state

# Manual rollback
kubectl get deployment <name> -o yaml > backup.yaml
# Edit backup.yaml to restore original values
kubectl apply -f backup.yaml
```

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPTIMIZER_API_URL=http://localhost:8000
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Run operator (requires kubeconfig)
kopf run --verbose --all-namespaces main.py
```

### Testing

```bash
# Create test workload
kubectl create deployment test-app --image=nginx --replicas=3

# Apply optimization
kubectl apply -f - <<EOF
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: test-optimization
spec:
  targetWorkload:
    name: test-app
    kind: Deployment
  optimizationType: ALL
  dryRun: true
  autoApply: false
EOF

# Watch status
kubectl get costopt test-optimization -w
```

## Future Enhancements

1. **Multi-Cluster Support**: Federate optimizations across clusters
2. **Cost Forecasting**: Predict future costs based on trends
3. **Policy Enforcement**: Organization-wide optimization policies
4. **Advanced Scheduling**: Time-based replica scaling
5. **Integration with Karpenter**: Node-level optimizations
6. **Slack/Email Notifications**: Alert on savings opportunities
7. **GitOps Integration**: ArgoCD/Flux synchronization
8. **Custom Metrics**: Support for custom optimization criteria

## License

Part of the K8s Cost Optimizer platform.
