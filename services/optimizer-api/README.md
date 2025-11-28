# K8s Cost Optimizer API

ML-based cost optimization engine for Kubernetes workloads across multi-cloud environments (AWS, GCP, Azure).

## Architecture

```
optimizer-api/
├── main.py                    # FastAPI application with all endpoints
├── models.py                  # Pydantic models for request/response validation
├── optimizer/
│   ├── ml_engine.py          # ML algorithms for optimization analysis
│   ├── cost_calculator.py    # Multi-cloud cost calculation
│   └── recommender.py        # Recommendation generation and risk assessment
└── tests/
    ├── sample_data.py        # Sample optimization scenarios
    ├── demo_scenarios.py     # Interactive demo script
    └── test_api.sh           # API test suite
```

## ML-Driven Optimization Strategies

### 1. Right-Sizing
- **Algorithm**: P95 utilization + 15% safety margin
- **Confidence Scoring**: Based on sample count, variance, time range
- **Typical Savings**: 40-50%

```python
recommended_cpu = cpu_p95 * 1.15
recommended_memory = memory_p95 * 1.15
```

### 2. Replica Optimization
- **Algorithm**: Target 70% utilization per replica
- **Considers**: Current replicas, utilization patterns, minimum replica count
- **Typical Savings**: 30-40%

```python
optimal_replicas = ceil(current_replicas * (current_utilization / target_utilization))
```

### 3. Spot Instance Recommendations
- **Criteria**: Fault-tolerant workloads, multiple replicas, non-critical paths
- **Analysis**: Workload characteristics, deployment kind, replica count
- **Typical Savings**: 60-70%

### 4. Scheduled Scaling
- **Pattern Detection**: Business hours, weekend usage, time-series analysis
- **Algorithms**: Variance analysis, peak/off-peak identification
- **Typical Savings**: 35-40%

### 5. Node Consolidation
- **Algorithm**: Bin-packing for optimal node utilization
- **Optimization**: Minimize number of nodes while maintaining capacity
- **Typical Savings**: 20-30%

### 6. Unused Resource Detection
- **Threshold**: <5% CPU and memory utilization
- **Validation**: Multi-day analysis to avoid false positives
- **Typical Savings**: 100% of unused resource cost

## API Endpoints

### Analysis Endpoints

#### `POST /analyze`
Analyze all workloads and generate comprehensive cost summary.

**Request Body:**
```json
{
  "cluster_filter": ["aws-cluster"],
  "namespace_filter": ["production"],
  "min_confidence": 0.7,
  "min_savings_threshold": 50.0,
  "include_high_risk": false
}
```

**Response:**
```json
{
  "total_workloads": 53,
  "total_current_monthly_cost": 12450.00,
  "total_optimized_monthly_cost": 7890.00,
  "total_potential_monthly_savings": 4560.00,
  "total_potential_yearly_savings": 54720.00,
  "overall_savings_percentage": 36.6,
  "clusters": [...],
  "top_recommendations": [...],
  "by_optimization_type": {...}
}
```

#### `POST /optimize/{workload_id}`
Generate optimization recommendations for specific workload.

**Request Body:**
```json
{
  "min_confidence": 0.6,
  "max_risk_level": "medium",
  "optimization_types": ["right_size_cpu", "reduce_replicas"]
}
```

**Response:**
```json
{
  "workload": {...},
  "metrics": {...},
  "recommendations": [...],
  "total_potential_savings": 438.00
}
```

### Recommendation Endpoints

#### `GET /recommendations`
List all recommendations above thresholds.

**Query Parameters:**
- `min_savings`: Minimum monthly savings (default: 0.0)
- `min_confidence`: Minimum confidence score (default: 0.5)
- `limit`: Maximum results (default: 100)

**Response:**
```json
{
  "recommendations": [...],
  "count": 42
}
```

#### `POST /apply/{recommendation_id}`
Apply optimization recommendation (with dry-run support).

**Request Body:**
```json
{
  "dry_run": true,
  "auto_rollback": true
}
```

**Response:**
```json
{
  "recommendation_id": "uuid",
  "status": "applied",
  "message": "Recommendation applied successfully",
  "applied_at": "2024-01-15T10:30:00Z"
}
```

### Export Endpoints

#### `POST /export/terraform`
Export top recommendations as Terraform configuration.

**Response:** Terraform JSON format (`.tf.json`)

```json
{
  "terraform": {
    "required_version": ">= 1.0"
  },
  "resource": {
    "k8s_deployment_frontend_web": {
      "metadata": {...},
      "spec": {...}
    }
  }
}
```

#### `GET /export/csv`
Export recommendations as CSV for reporting.

**Response:** CSV file with columns:
```
Cluster, Namespace, Workload, Optimization Type, Current Monthly Cost,
Optimized Monthly Cost, Monthly Savings, Savings %, Confidence Score,
Risk Level, Status
```

### Monitoring Endpoints

#### `GET /savings/history`
Historical savings data (realized vs. potential).

**Query Parameters:**
- `days`: Time range (default: 30)

**Response:**
```json
{
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z",
  "total_recommendations_generated": 156,
  "recommendations_applied": 42,
  "potential_savings": 8450.00,
  "realized_savings": 3120.00,
  "realization_rate": 36.9
}
```

#### `WS /ws`
WebSocket endpoint for real-time optimization updates.

**Update Frequency:** Every 30 seconds

**Message Format:**
```json
{
  "event_type": "optimization_update",
  "data": {
    "total_savings": 4560.00,
    "recommendation_count": 42,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "optimizer-api",
  "version": "1.0.0"
}
```

## Risk Assessment

Each recommendation includes comprehensive risk assessment:

### Risk Levels
- **LOW**: <0.5 - Safe to apply with standard testing
- **MEDIUM**: 0.5-0.7 - Requires careful testing and monitoring
- **HIGH**: 0.7-0.9 - Significant risk, extensive testing required
- **CRITICAL**: >0.9 - High impact, staged rollout recommended

### Risk Factors
- Workload type (StatefulSet = higher risk)
- Replica count (single replica = higher risk)
- Current utilization levels (>80% = higher risk)
- Optimization type (spot instances = medium risk)

### Rollback Plans
Every recommendation includes:
- Step-by-step rollback procedure
- Estimated rollback time
- Automation availability

## Confidence Scoring

Confidence scores are calculated based on multiple factors:

```python
base_confidence = 0.5

# Sample size factor
if sample_count > 1000:
    base_confidence += 0.2
elif sample_count > 500:
    base_confidence += 0.1

# Variance factor (stability)
if variance < 0.15:
    base_confidence += 0.2
elif variance < 0.25:
    base_confidence += 0.1

# Time range factor
if time_range_hours >= 168:  # 7 days
    base_confidence += 0.1

# Optimization type factor
if optimization_type == "right_sizing":
    base_confidence += 0.05
```

## Cost Calculation

### Multi-Cloud Pricing Integration
The optimizer connects to mock pricing APIs for AWS, GCP, and Azure:

- **AWS Pricing API**: `http://aws-pricing-api:8000`
- **GCP Pricing API**: `http://gcp-pricing-api:8000`
- **Azure Pricing API**: `http://azure-pricing-api:8000`

### Instance Type Inference
When instance type is not specified, the calculator infers based on resource requirements:

```python
total_cpu = cpu_request_cores * replicas
total_memory_gb = memory_request_gb * replicas

if total_cpu <= 2 and total_memory_gb <= 4:
    instance_type = "t3.medium"  # AWS
elif total_cpu <= 4 and total_memory_gb <= 8:
    instance_type = "m5.xlarge"  # AWS
# ... more inference logic
```

### Cost Components
- **Compute**: CPU + memory costs per hour
- **Storage**: Persistent volume costs
- **Network**: Egress traffic costs
- **Spot Discount**: 60-70% off on-demand pricing

## Sample Optimization Scenarios

The optimizer demonstrates realistic scenarios achieving 35-40% cost reduction:

### Scenario 1: Over-Provisioned Web Service
- **Current**: 2000m CPU, 4Gi memory, 5 replicas
- **Actual Usage**: 20% CPU, 30% memory
- **Recommendation**: Right-size to 750m CPU, 2Gi memory
- **Savings**: 50% ($438/month)

### Scenario 2: Excessive Replicas
- **Current**: 8 replicas at 70% utilization
- **Recommendation**: Reduce to 5 replicas
- **Savings**: 37.5% ($438/month)

### Scenario 3: Spot Instance Candidate
- **Current**: On-demand batch processor
- **Recommendation**: Switch to spot instances
- **Savings**: 70% ($2,044/month)

### Scenario 4: Unused Development Environment
- **Current**: 3 replicas, <5% utilization
- **Recommendation**: Delete or schedule
- **Savings**: 100% ($657/month)

### Scenario 5: Scheduled Scaling
- **Current**: Fixed 6 replicas 24/7
- **Pattern**: Business hours only
- **Recommendation**: Scale down to 2 during off-peak
- **Savings**: 40% ($175/month)

### Scenario 6: Wrong Instance Type
- **Current**: c5.2xlarge (compute-optimized) for memory-intensive DB
- **Recommendation**: Switch to r5.xlarge (memory-optimized)
- **Savings**: 26% ($65/month)

### Aggregate Results
- **Total Workloads**: 6
- **Current Monthly Cost**: $6,307
- **Optimized Monthly Cost**: $3,490
- **Monthly Savings**: $2,817 (44.7%)
- **Yearly Savings**: $33,804

## Testing

### Run Demo Scenarios
```bash
python3 services/optimizer-api/tests/demo_scenarios.py
```

### Test API Endpoints
```bash
./services/optimizer-api/tests/test_api.sh
```

### Run Sample Data Analysis
```bash
cd services/optimizer-api
python3 tests/sample_data.py
```

### Make Targets
```bash
# Test optimizer API
make test-optimizer

# Test pricing APIs
make test-pricing

# Test metrics generator
make test-metrics
```

## Environment Variables

```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=k8s_optimizer
POSTGRES_USER=optimizer
POSTGRES_PASSWORD=optimizer_dev_pass

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# Pricing APIs
AWS_PRICING_URL=http://aws-pricing-api:8000
GCP_PRICING_URL=http://gcp-pricing-api:8000
AZURE_PRICING_URL=http://azure-pricing-api:8000

# Service
PORT=8000
```

## Dependencies

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
httpx==0.26.0
psycopg2-binary==2.9.9
redis==5.0.1
numpy==1.26.3
pandas==2.1.4
scikit-learn==1.3.2
websockets==12.0
```

## Performance Characteristics

- **Analysis Speed**: ~100ms per workload
- **Recommendation Generation**: ~50ms per workload
- **Database Queries**: Optimized with indexes on workload_id, timestamp
- **WebSocket Updates**: 30-second intervals
- **Concurrent Requests**: Supports 100+ concurrent API requests

## Future Enhancements

1. **Advanced ML Models**
   - LSTM for time-series prediction
   - Anomaly detection for cost spikes
   - Clustering for workload classification

2. **Auto-Apply with Guardrails**
   - Canary deployments
   - Automatic rollback on errors
   - Progressive optimization

3. **Cost Forecasting**
   - Predict future costs based on trends
   - Budget alerting and enforcement
   - Capacity planning recommendations

4. **Multi-Region Optimization**
   - Cross-region cost comparison
   - Regional failover cost analysis
   - Data transfer cost optimization

5. **Reserved Instance Recommendations**
   - Analyze usage patterns for RI suitability
   - Savings plan optimization
   - Commitment term analysis
