# Metrics Generator Service

Generates realistic Kubernetes workload metrics for cost optimization analysis across multi-cloud environments.

## Overview

The Metrics Generator creates synthetic but realistic resource usage data for Kubernetes workloads distributed across simulated AWS, GCP, and Azure clusters. It generates time-series metrics with realistic patterns including business hours peaks, weekend reductions, growth trends, and anomalies.

## Features

- **53+ Diverse Workloads**: Web services, databases, batch jobs, microservices, ML workloads, caching, messaging, and monitoring
- **Realistic Patterns**: Business hours (9am-5pm peaks), weekend reduction (30% lower), gradual growth trends
- **Random Variance**: Spikes and anomalies to simulate real-world conditions
- **Multi-Cloud Distribution**: Workloads distributed across AWS (25), GCP (15), Azure (13) clusters
- **Historical Data**: Generates 7 days of historical data on startup
- **Prometheus Export**: Exposes metrics in Prometheus format on port 8001
- **PostgreSQL Storage**: Stores all metrics in PostgreSQL for analysis and reporting

## Components

### workload_generator.py

Creates diverse workload definitions including:
- Web services (frontend, API gateway, admin panel, mobile API)
- Databases (PostgreSQL, Redis, MongoDB, Elasticsearch)
- Batch jobs (reports, exports, backups)
- Microservices (15 different services)
- ML workloads (training, inference, feature engineering)
- Cache services (Memcached, Varnish)
- Message queues (RabbitMQ, Kafka)
- Monitoring stack (Prometheus, Grafana, Alertmanager)

### metrics_simulator.py

Generates realistic time-series metrics with:
- **CPU Usage**: Based on workload profile with business hours patterns
- **Memory Usage**: Memory-intensive workloads with gradual growth
- **Network Traffic**: RX/TX bytes based on workload type
- **Patterns**:
  - Business hours: 9am-5pm peaks with sine curve
  - Weekend reduction: 30% lower on Sat/Sun
  - Nightly jobs: Peak usage 12am-6am
  - Growth trends: Gradual increase over time
  - Spikes: Random 2% chance of 1.5-3x usage spike

### main.py

Orchestrates metric generation:
- Initializes 53 workloads in database
- Generates 7 days of historical metrics (30-minute intervals)
- Continuously generates current metrics (60-second intervals)
- Exposes Prometheus metrics endpoint
- Stores all metrics in PostgreSQL

## Configuration

Environment variables:

```bash
# PostgreSQL connection
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=k8s_optimizer
POSTGRES_USER=optimizer
POSTGRES_PASSWORD=optimizer_dev_pass

# Metrics generation
METRICS_PORT=8001
GENERATION_INTERVAL=60           # Seconds between metric generation
GENERATE_HISTORICAL=true         # Generate historical data on startup
HISTORICAL_DAYS=7                # Days of historical data to generate
```

## Exposed Metrics

The service exposes the following Prometheus metrics on `:8001/metrics`:

```
k8s_workload_cpu_usage_cores{cluster, namespace, workload, kind}
k8s_workload_memory_usage_bytes{cluster, namespace, workload, kind}
k8s_workload_network_rx_bytes{cluster, namespace, workload, kind}
k8s_workload_network_tx_bytes{cluster, namespace, workload, kind}
metrics_generator_total{cluster}
```

## Database Schema

Stores metrics in PostgreSQL tables:
- `clusters`: Cluster metadata (aws-cluster, gcp-cluster, azure-cluster)
- `workloads`: Workload definitions with resource requests/limits
- `metrics`: Time-series resource usage data

## Running

### With Docker Compose

```bash
docker-compose up metrics-generator
```

### Standalone

```bash
cd services/metrics-generator
pip install -r requirements.txt
python main.py
```

## Workload Distribution

**AWS Cluster (25 workloads)**:
- Frontend web, API gateway, admin panel, static CDN, mobile API
- PostgreSQL primary, Redis cache, MongoDB
- Batch jobs and microservices (user, auth, payment, etc.)

**GCP Cluster (15 workloads)**:
- PostgreSQL replica, Elasticsearch, batch jobs
- Microservices (notification, inventory, order, etc.)
- ML workloads (training, inference)

**Azure Cluster (13 workloads)**:
- Microservices (shipping, analytics, recommendation, etc.)
- Cache services (Memcached, Varnish)
- Message queues (RabbitMQ, Kafka)
- Monitoring stack (Prometheus, Grafana, Alertmanager, Node Exporter)

## Resource Profiles

- **CPU Intensive**: Higher CPU usage, optimized for compute
- **Memory Intensive**: Higher memory usage, databases and caches
- **Balanced**: Equal CPU and memory usage
- **Low Usage**: Minimal resource consumption

## Scaling Patterns

- **business_hours**: Peak 9am-5pm, low overnight
- **nightly**: Peak 12am-6am, low during day
- **hourly**: Spike at top of each hour
- **sporadic**: Random usage spikes
- **weekend_low**: Reduced usage on weekends
- **steady**: Consistent usage 24/7

## Monitoring

Access Prometheus metrics:
```bash
curl http://localhost:8001/metrics
```

Query specific workload:
```bash
curl -s http://localhost:8001/metrics | grep 'k8s_workload_cpu_usage_cores{cluster="aws-cluster",namespace="production",workload="frontend-web"}'
```

## Development

Run tests:
```bash
pytest tests/ -v
```

Generate metrics for specific timeframe:
```python
from metrics_simulator import MetricsSimulator
from workload_generator import WorkloadGenerator
from datetime import datetime, timedelta

sim = MetricsSimulator()
gen = WorkloadGenerator()
workloads = gen.get_all_workloads()

start = datetime.utcnow() - timedelta(days=1)
end = datetime.utcnow()

for workload in workloads[:5]:
    metrics = sim.generate_historical_metrics(workload, start, end, interval_minutes=15)
    print(f"{workload['name']}: {len(metrics)} data points")
```

## Performance

- Initial startup: ~30-60 seconds (including historical data generation)
- Historical data generation: ~7 days @ 30-min intervals = ~336 points per workload
- Total historical metrics: 53 workloads × 336 points = ~17,808 metrics
- Continuous generation: 53 metrics per minute
- Database inserts: Batched in groups of 1000 for performance

## Health Check

The service includes a health check endpoint:
```bash
curl http://localhost:8001/metrics
```

If the service is healthy, it returns Prometheus metrics. The Docker health check verifies this endpoint every 30 seconds.
