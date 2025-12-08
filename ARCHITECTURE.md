# Architecture Documentation

## System Overview

The Kubernetes Cost Optimizer is built as a cloud-native, microservices-based platform designed for scalability, reliability, and multi-tenancy. This document outlines the architectural decisions, component interactions, and design patterns used throughout the system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users / Teams                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                            │
├──────────────────────┬──────────────────────────────────────────┤
│  React Dashboard     │  Grafana Dashboards  │  API Docs/Swagger │
│  (Port 3000)         │  (Port 3000)         │  (Port 8000/docs) │
└──────────────────────┴──────────────────────┴───────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer                   │
│                         (Nginx / Ingress)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
├──────────────────────┬──────────────────────────────────────────┤
│  Optimizer API       │  K8s Operator     │  ML Engine           │
│  (FastAPI/Python)    │  (Go)             │  (Python/Scikit)     │
│                      │                   │                       │
│  - Cost Analysis     │  - Workload Watch │  - Prediction        │
│  - Recommendations   │  - Auto-Apply     │  - Anomaly Detection │
│  - Pricing APIs      │  - CRD Management │  - Model Training    │
└──────────────────────┴──────────────────┴───────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                         │
├──────────────────────┬──────────────────────────────────────────┤
│  Metrics Collector   │  Pricing Collector │  Event Collector    │
│  (Prometheus)        │  (APIs)            │  (K8s Events)       │
└──────────────────────┴──────────────────┴───────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                 │
├──────────────────────┬──────────────────┬───────────────────────┤
│  PostgreSQL          │  Redis           │  MinIO/S3             │
│  - Workload metadata │  - Cache         │  - Reports            │
│  - Recommendations   │  - Job Queue     │  - ML Models          │
│  - Cost history      │  - Pub/Sub       │  - Backups            │
└──────────────────────┴──────────────────┴───────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
├──────────────────────┬──────────────────┬───────────────────────┤
│  AWS EKS             │  GCP GKE         │  Azure AKS            │
│  (Managed K8s)       │  (Managed K8s)   │  (Managed K8s)        │
└──────────────────────┴──────────────────┴───────────────────────┘
```

## Core Components

### 1. Optimizer API (FastAPI)

**Purpose:** Central API service handling all business logic

**Responsibilities:**
- Cost analysis and calculation
- Recommendation generation
- Pricing API integration (AWS, GCP, Azure)
- User authentication and authorization
- WebSocket for real-time updates

**Technology Choices:**
- **FastAPI**: High performance, async support, auto-documentation
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **httpx**: Async HTTP client for external APIs

**Endpoints:**
```
POST   /api/v1/analysis          - Start cost analysis
GET    /api/v1/analysis/{id}      - Get analysis status
GET    /api/v1/recommendations    - List recommendations
POST   /api/v1/recommendations/{id}/apply - Apply recommendation
GET    /api/v1/costs/current      - Current costs
GET    /api/v1/costs/history      - Historical costs
GET    /api/v1/costs/forecast     - Cost forecast
POST   /api/v1/clusters           - Register cluster
GET    /api/v1/pricing/compare    - Compare cloud pricing
```

### 2. Kubernetes Operator (Go)

**Purpose:** Kubernetes-native controller for automated optimization

**Responsibilities:**
- Watch workloads across clusters
- Apply approved recommendations
- Manage Custom Resource Definitions (CRDs)
- Handle rollbacks on failures
- Report status back to API

**Technology Choices:**
- **controller-runtime**: Kubernetes controller framework
- **client-go**: Kubernetes API client
- **Operator SDK**: Scaffolding and best practices

**CRDs:**
```yaml
# OptimizationPolicy CRD
apiVersion: optimizer.k8s.io/v1alpha1
kind: OptimizationPolicy
metadata:
  name: production-auto-optimize
spec:
  targetNamespaces:
    - production
  autoApprove:
    minConfidence: 0.9
    maxRiskLevel: low
  rolloutStrategy:
    type: canary
    steps:
      - replicas: 20%
        duration: 5m
      - replicas: 50%
        duration: 10m
      - replicas: 100%

# OptimizationRecommendation CRD
apiVersion: optimizer.k8s.io/v1alpha1
kind: OptimizationRecommendation
metadata:
  name: web-app-rightsizing
spec:
  targetWorkload:
    kind: Deployment
    name: web-app
    namespace: production
  type: right-sizing
  changes:
    cpu: "500m"
    memory: "1Gi"
  estimatedSavings: 450.50
  confidence: 0.92
status:
  phase: Pending
  approvedBy: admin@example.com
  appliedAt: "2024-01-15T10:30:00Z"
```

### 3. ML Engine (Python)

**Purpose:** Machine learning for predictions and anomaly detection

**Responsibilities:**
- Usage pattern recognition
- Anomaly detection
- Cost forecasting
- Workload classification
- Confidence scoring

**Technology Choices:**
- **Scikit-learn**: Traditional ML algorithms
- **Prophet**: Time series forecasting
- **NumPy/Pandas**: Data manipulation
- **MLflow**: Model versioning and tracking

**Models:**
1. **Usage Predictor**: LSTM for resource usage forecasting
2. **Anomaly Detector**: Isolation Forest for unusual patterns
3. **Workload Classifier**: Random Forest for workload categorization
4. **Cost Forecaster**: Prophet for cost predictions

### 4. Data Collection Layer

#### Metrics Collector (Prometheus)
```yaml
# Scrape configuration
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
```

**Metrics Collected:**
- `container_cpu_usage_seconds_total`
- `container_memory_working_set_bytes`
- `container_network_receive_bytes_total`
- `container_network_transmit_bytes_total`
- `kube_pod_container_resource_requests`
- `kube_pod_container_resource_limits`

#### Pricing Collector

**AWS Pricing API:**
```python
# Fetch EC2 pricing
pricing_client = boto3.client('pricing', region_name='us-east-1')
response = pricing_client.get_products(
    ServiceCode='AmazonEC2',
    Filters=[
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.medium'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'}
    ]
)
```

**GCP Pricing API:**
```python
# Cloud Billing API
service = build('cloudbilling', 'v1', credentials=creds)
services = service.services().list().execute()
```

**Azure Pricing API:**
```python
# Retail Prices API
response = requests.get(
    'https://prices.azure.com/api/retail/prices',
    params={
        'armRegionName': 'eastus',
        'armSkuName': 'Standard_D2s_v3'
    }
)
```

## Data Flow

### 1. Analysis Workflow

```
┌──────────┐   1. Request    ┌─────────────┐
│  User/   │─────Analysis────►│ Optimizer   │
│Dashboard │                  │    API      │
└──────────┘                  └──────┬──────┘
                                     │
                              2. Create Job
                                     │
                                     ▼
                              ┌─────────────┐
                              │   Redis     │
                              │ Job Queue   │
                              └──────┬──────┘
                                     │
                              3. Process Job
                                     │
                                     ▼
                     ┌───────────────┴───────────────┐
                     │                               │
                     ▼                               ▼
              ┌─────────────┐              ┌─────────────┐
              │  Metrics    │              │  Pricing    │
              │  Collector  │              │  Collector  │
              └──────┬──────┘              └──────┬──────┘
                     │                            │
              4. Fetch Metrics          5. Fetch Prices
                     │                            │
                     ▼                            ▼
              ┌─────────────┐              ┌─────────────┐
              │ Prometheus  │              │ Cloud APIs  │
              └──────┬──────┘              └──────┬──────┘
                     │                            │
                     └────────────┬───────────────┘
                                  │
                          6. Analyze & Generate
                                  │
                                  ▼
                          ┌─────────────┐
                          │  ML Engine  │
                          └──────┬──────┘
                                 │
                         7. Save Results
                                 │
                                 ▼
                          ┌─────────────┐
                          │ PostgreSQL  │
                          └──────┬──────┘
                                 │
                         8. Notify Complete
                                 │
                                 ▼
                          ┌─────────────┐
                          │  WebSocket  │
                          │   Pub/Sub   │
                          └──────┬──────┘
                                 │
                         9. Update UI
                                 │
                                 ▼
                          ┌─────────────┐
                          │  Dashboard  │
                          └─────────────┘
```

### 2. Recommendation Application Workflow

```
User approves      ┌─────────────┐
recommendation ───►│ Optimizer   │
                   │    API      │
                   └──────┬──────┘
                          │
                   1. Validate
                          │
                          ▼
                   ┌─────────────┐
                   │ Permission  │
                   │   Check     │
                   └──────┬──────┘
                          │
                   2. Create CRD
                          │
                          ▼
                   ┌─────────────┐
                   │ Kubernetes  │
                   │   Operator  │
                   └──────┬──────┘
                          │
                   3. Apply Changes
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       ┌─────────────┐         ┌─────────────┐
       │   Canary    │         │   Monitor   │
       │   Deploy    │         │   Health    │
       └──────┬──────┘         └──────┬──────┘
              │                       │
              │  4. Check Health      │
              └───────────┬───────────┘
                          │
                    Success? ◄─────┐
                          │        │
                   Yes    │   No   │
                          │        │
                          ▼        │
                   ┌─────────────┐ │
                   │  Continue   │ │
                   │  Rollout    │ │
                   └──────┬──────┘ │
                          │        │
                          │    ┌───┴───────┐
                          │    │  Rollback │
                          │    └───────────┘
                          │
                   5. Complete
                          │
                          ▼
                   ┌─────────────┐
                   │   Update    │
                   │   Status    │
                   └──────┬──────┘
                          │
                   6. Track Savings
                          │
                          ▼
                   ┌─────────────┐
                   │ PostgreSQL  │
                   └─────────────┘
```

## Database Schema

### PostgreSQL Tables

```sql
-- Clusters
CREATE TABLE clusters (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Analyses
CREATE TABLE analyses (
    id UUID PRIMARY KEY,
    cluster_id UUID REFERENCES clusters(id),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    workloads_analyzed INTEGER,
    total_cost_current DECIMAL(12,2),
    total_cost_optimized DECIMAL(12,2),
    metadata JSONB
);

-- Recommendations
CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id),
    type VARCHAR(50) NOT NULL,
    workload_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    monthly_savings DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    applied_at TIMESTAMP,
    details JSONB NOT NULL
);

-- Cost History
CREATE TABLE daily_costs (
    id BIGSERIAL PRIMARY KEY,
    cluster_id UUID REFERENCES clusters(id),
    date DATE NOT NULL,
    compute_cost DECIMAL(10,2),
    storage_cost DECIMAL(10,2),
    network_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    metadata JSONB,
    UNIQUE(cluster_id, date)
);

-- Workload Metrics (partitioned by time)
CREATE TABLE workload_metrics (
    timestamp TIMESTAMP NOT NULL,
    cluster_id UUID NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    workload_name VARCHAR(255) NOT NULL,
    cpu_usage DECIMAL(10,2),
    memory_usage BIGINT,
    network_in BIGINT,
    network_out BIGINT
) PARTITION BY RANGE (timestamp);

-- Create partitions for each month
CREATE TABLE workload_metrics_2024_01 PARTITION OF workload_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Redis Data Structures

```redis
# Cache pricing data (TTL: 1 hour)
SET pricing:aws:t3.medium:us-east-1 "0.0416" EX 3600

# Job queue
LPUSH jobs:analysis "analysis-uuid-123"
BRPOP jobs:analysis 0

# Pub/Sub for real-time updates
PUBLISH analysis:updates '{"id": "123", "status": "completed"}'

# Rate limiting (token bucket)
INCR ratelimit:api:user-123
EXPIRE ratelimit:api:user-123 60

# Session storage
SETEX session:abc123 1800 '{"user_id": "456", "role": "admin"}'
```

## Design Decisions

### 1. Why FastAPI over Django/Flask?

**Chosen:** FastAPI

**Rationale:**
- ✅ Async/await support (critical for concurrent API calls)
- ✅ Auto-generated OpenAPI docs
- ✅ Built-in data validation with Pydantic
- ✅ High performance (comparable to Node.js/Go)
- ✅ Type hints improve code quality

**Trade-offs:**
- ❌ Smaller ecosystem than Django
- ❌ Less built-in features (admin, auth)

### 2. Why PostgreSQL over MySQL/MongoDB?

**Chosen:** PostgreSQL

**Rationale:**
- ✅ JSONB for flexible schema
- ✅ Table partitioning for time-series data
- ✅ Advanced indexing (GIN, GIST)
- ✅ Full-text search
- ✅ Strong consistency

**Trade-offs:**
- ❌ More complex than MySQL
- ❌ Higher resource usage

### 3. Why Redis over Memcached?

**Chosen:** Redis

**Rationale:**
- ✅ Rich data structures (lists, sets, sorted sets)
- ✅ Pub/Sub for real-time updates
- ✅ Persistence options
- ✅ Atomic operations
- ✅ Lua scripting

**Trade-offs:**
- ❌ Single-threaded (though not an issue at our scale)
- ❌ Higher memory usage

### 4. Why Go for Operator over Python?

**Chosen:** Go

**Rationale:**
- ✅ Native Kubernetes ecosystem
- ✅ Excellent concurrency (goroutines)
- ✅ Low resource usage
- ✅ Fast compilation
- ✅ Strong typing

**Trade-offs:**
- ❌ Steeper learning curve
- ❌ More verbose than Python

### 5. Why Microservices over Monolith?

**Chosen:** Microservices

**Rationale:**
- ✅ Independent scaling (API vs ML engine)
- ✅ Technology flexibility (Python + Go)
- ✅ Isolated failures
- ✅ Team autonomy

**Trade-offs:**
- ❌ Increased complexity
- ❌ Distributed system challenges
- ❌ Higher operational overhead

## Security Architecture

### Authentication & Authorization

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. Login
     ▼
┌──────────────┐
│  API Gateway │
└────┬─────────┘
     │ 2. Generate JWT
     ▼
┌──────────────┐
│  Auth Service│
└────┬─────────┘
     │ 3. Return Token
     ▼
┌──────────────┐
│   Client     │
│ (stores JWT) │
└────┬─────────┘
     │ 4. API Request + JWT
     ▼
┌──────────────┐
│  API Gateway │
│ (verify JWT) │
└────┬─────────┘
     │ 5. Forward Request
     ▼
┌──────────────┐
│ Backend API  │
└──────────────┘
```

**JWT Claims:**
```json
{
  "sub": "user-123",
  "email": "user@example.com",
  "role": "admin",
  "teams": ["platform", "sre"],
  "exp": 1704067200,
  "iat": 1704063600
}
```

**RBAC Roles:**
- **Admin**: Full access
- **Engineer**: View, apply recommendations
- **Viewer**: Read-only access
- **Operator**: Auto-apply within policies

### Network Security

```
┌─────────────────────────────────────────┐
│              Internet                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│      Cloud Load Balancer (TLS)           │
│      - SSL termination                   │
│      - DDoS protection                   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│      Ingress Controller (NGINX)          │
│      - Rate limiting                     │
│      - WAF rules                         │
└──────────────┬───────────────────────────┘
               │
          ┌────┴────┐
          │         │
          ▼         ▼
┌──────────────┐ ┌──────────────┐
│  Dashboard   │ │  API Service │
│  (Public)    │ │  (Private)   │
└──────────────┘ └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  PostgreSQL  │
                 │  (Private)   │
                 └──────────────┘
```

**Network Policies:**
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
```

## Scalability Considerations

### Horizontal Scaling

| Component | Strategy | Metric |
|-----------|----------|--------|
| API | HPA | CPU > 70% or Requests > 1000/min |
| ML Engine | Job-based | Queue depth > 100 |
| Operator | Leader election | Single active instance |
| Dashboard | Static assets via CDN | N/A |

### Data Partitioning

**Time-series data** (workload_metrics):
- Partitioned by month
- Automatic partition creation
- Retention: 90 days
- Archive to S3 after 30 days

**Hot/Cold data separation:**
- Hot (< 7 days): PostgreSQL
- Warm (7-30 days): PostgreSQL (compressed)
- Cold (> 30 days): S3/Parquet

### Caching Strategy

```python
# Multi-level caching
class CostCalculator:
    @lru_cache(maxsize=1000)  # L1: In-memory
    def calculate_instance_cost(self, instance_type, region):
        # L2: Redis cache
        cached = redis.get(f"price:{instance_type}:{region}")
        if cached:
            return float(cached)

        # L3: Database
        price = db.query_price(instance_type, region)
        if price:
            redis.setex(f"price:{instance_type}:{region}", 3600, price)
            return price

        # L4: External API
        price = pricing_api.get_price(instance_type, region)
        redis.setex(f"price:{instance_type}:{region}", 3600, price)
        return price
```

## Monitoring & Observability

### Metrics (Prometheus)

**Application metrics:**
```python
# Custom metrics
recommendations_total = Counter(
    'recommendations_total',
    'Total recommendations generated',
    ['type', 'status']
)

analysis_duration = Histogram(
    'analysis_duration_seconds',
    'Time spent analyzing workloads',
    ['cluster']
)

cost_savings = Gauge(
    'cost_savings_monthly_dollars',
    'Estimated monthly savings',
    ['cluster', 'namespace']
)
```

### Logging (Structured)

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "optimizer-api",
  "trace_id": "abc123",
  "span_id": "def456",
  "user_id": "user-789",
  "message": "Analysis completed",
  "context": {
    "analysis_id": "analysis-123",
    "workloads_analyzed": 45,
    "duration_ms": 3456,
    "savings_found": 2500.50
  }
}
```

### Tracing (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("analyze_workload")
def analyze_workload(workload_id):
    span = trace.get_current_span()
    span.set_attribute("workload.id", workload_id)

    with tracer.start_as_current_span("fetch_metrics"):
        metrics = fetch_metrics(workload_id)

    with tracer.start_as_current_span("calculate_recommendation"):
        recommendation = calculate(metrics)

    return recommendation
```

## Disaster Recovery

### Backup Strategy

| Data Type | Frequency | Retention | Method |
|-----------|-----------|-----------|--------|
| PostgreSQL | Hourly | 7 days | WAL archiving |
| PostgreSQL (full) | Daily | 30 days | pg_dump to S3 |
| Redis | 6 hours | 24 hours | RDB snapshots |
| Configuration | On change | Infinite | Git |

### Recovery Procedures

**RTO (Recovery Time Objective):** 1 hour
**RPO (Recovery Point Objective):** 1 hour

```bash
# Database recovery
aws s3 cp s3://backups/postgres/latest.dump /tmp/
psql -U optimizer -d k8s_optimizer < /tmp/latest.dump

# Redis recovery
redis-cli --rdb /var/lib/redis/dump.rdb

# Application redeployment
kubectl apply -f infrastructure/kubernetes/
```

## Future Architecture Enhancements

### Planned Improvements

1. **Event Sourcing**
   - Replace CRUD with event store
   - Enable time-travel debugging
   - Better audit trails

2. **GraphQL API**
   - Add GraphQL alongside REST
   - Client-driven queries
   - Reduce over-fetching

3. **Stream Processing**
   - Apache Kafka for event streaming
   - Real-time analytics
   - Complex event processing

4. **Service Mesh**
   - Istio for traffic management
   - mTLS between services
   - Advanced routing

5. **Multi-Region**
   - Active-active deployment
   - Cross-region replication
   - Geo-routing

---

**Last Updated:** December 2024
**Version:** 1.0
**Maintainer:** Platform Team
