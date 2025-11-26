# Multi-Cloud Kubernetes Cost Optimizer

A portfolio project demonstrating DevOps and infrastructure skills through local simulation of multi-cloud Kubernetes environments with ML-based cost optimization recommendations.

## Overview

This platform simulates AWS, GCP, and Azure Kubernetes clusters locally and provides:
- Real-time cost analysis of Kubernetes workloads
- ML-based optimization recommendations
- Multi-cloud comparison and insights
- Comprehensive monitoring and visualization

## Architecture

- **Backend**: Python (FastAPI), Go (Kubernetes Operator)
- **Frontend**: React with Chart.js
- **Infrastructure**: Docker, Kind, Terraform, Helm
- **Data**: PostgreSQL, Redis, MinIO
- **Monitoring**: Prometheus, Grafana

## Prerequisites

Ensure you have the following installed:

- **Docker** (v20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+): Usually bundled with Docker Desktop
- **Kind** (v0.20+): [Install Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **kubectl** (v1.28+): [Install kubectl](https://kubernetes.io/docs/tasks/tools/)
- **Make**: Usually pre-installed on Linux/macOS

Verify installations:
```bash
docker --version
docker-compose --version  # or: docker compose version
kind --version
kubectl version --client
make --version
```

## Quick Start

### 1. Clone and Setup Environment

```bash
cd k8s-cost-optimizer
cp .env.example .env
```

Edit `.env` if you want to customize ports or credentials.

### 2. Start Infrastructure

```bash
# Complete setup (creates clusters + starts services)
make setup
make start

# Or run individually
make clusters    # Create Kind clusters only
make start       # Start Docker services only
```

### 3. Verify Installation

```bash
make health-check
make status
```

## Infrastructure Components

### Docker Services

| Service | Port | Credentials | Purpose |
|---------|------|-------------|---------|
| Grafana | 3000 | admin/admin123 | Visualization dashboard |
| Prometheus | 9090 | - | Metrics collection |
| MinIO | 9000, 9001 | minioadmin/minioadmin123 | Object storage |
| PostgreSQL | 5432 | optimizer/optimizer_dev_pass | Data persistence |
| Redis | 6379 | - | Caching & queues |

### Kubernetes Clusters

| Cluster | Provider | Nodes | Context |
|---------|----------|-------|---------|
| aws-cluster | AWS | 3 | kind-aws-cluster |
| gcp-cluster | GCP | 2 | kind-gcp-cluster |
| azure-cluster | Azure | 2 | kind-azure-cluster |

## Usage

### Managing Services

```bash
# Start all services
make start

# Stop all services
make stop

# View logs
make logs

# Check health
make health-check

# View status
make status

# Complete cleanup
make clean
```

### Working with Clusters

```bash
# List all clusters
kind get clusters

# Interact with specific cluster
kubectl --context kind-aws-cluster get nodes
kubectl --context kind-gcp-cluster get pods -A
kubectl --context kind-azure-cluster get namespaces

# Delete and recreate clusters
make clusters-clean
make clusters
```

### Accessing Services

#### Grafana
```bash
# URL: http://localhost:3000
# Username: admin
# Password: admin123
```

#### Prometheus
```bash
# URL: http://localhost:9090
# Query examples available in UI
```

#### MinIO Console
```bash
# URL: http://localhost:9001
# Username: minioadmin
# Password: minioadmin123
```

#### PostgreSQL
```bash
# Connect via psql
docker exec -it k8s-optimizer-postgres psql -U optimizer -d k8s_optimizer

# Or use any PostgreSQL client
# Host: localhost
# Port: 5432
# Database: k8s_optimizer
# Username: optimizer
# Password: optimizer_dev_pass
```

## Project Structure

```
k8s-cost-optimizer/
├── config/                    # Configuration files
│   ├── grafana/              # Grafana provisioning
│   │   └── datasources.yml
│   ├── kind/                 # Kind cluster configs
│   │   ├── aws-cluster.yaml
│   │   ├── gcp-cluster.yaml
│   │   └── azure-cluster.yaml
│   └── prometheus.yml        # Prometheus config
├── scripts/                   # Automation scripts
│   ├── setup-clusters.sh     # Create Kind clusters
│   ├── cleanup.sh            # Remove clusters
│   ├── health-check.sh       # Verify services
│   └── init-db.sh            # Initialize database
├── services/                  # Application services (future)
├── manifests/                 # Kubernetes manifests (future)
├── tests/                     # Tests (future)
├── docker-compose.yml         # Service definitions
├── Makefile                   # Build automation
└── .env.example              # Environment template
```

## Database Schema

The PostgreSQL database includes tables for:
- **clusters**: Cluster metadata and configuration
- **workloads**: Kubernetes workload information
- **metrics**: Time-series resource usage data
- **cost_estimates**: Calculated cost data
- **recommendations**: ML-generated optimization suggestions

View schema:
```bash
docker exec -it k8s-optimizer-postgres psql -U optimizer -d k8s_optimizer -c "\dt"
```

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check for port conflicts
lsof -i :3000,5432,6379,9000,9001,9090

# Restart services
make stop
make start
```

### Clusters won't create
```bash
# Check Kind installation
kind version

# Check Docker resources
docker info

# Clean and retry
make clusters-clean
make clusters
```

### Health check failures
```bash
# View service logs
docker-compose logs postgres
docker-compose logs prometheus

# Check individual service
docker exec k8s-optimizer-postgres pg_isready -U optimizer
```

### Database connection issues
```bash
# Verify PostgreSQL is running
docker exec k8s-optimizer-postgres pg_isready -U optimizer

# Reinitialize database
docker-compose down -v
docker-compose up -d postgres
```

## Development Workflow

1. Start infrastructure: `make setup && make start`
2. Verify health: `make health-check`
3. Develop services in `services/` directory
4. Deploy to clusters using `manifests/`
5. Monitor via Grafana dashboard
6. Run tests from `tests/` directory

## Cleanup

```bash
# Stop services only
make stop

# Complete cleanup (removes clusters and volumes)
make clean
```

## Next Steps

After infrastructure setup, proceed with:
1. Backend API service implementation
2. Kubernetes operator development
3. Frontend dashboard creation
4. ML model integration
5. Custom Grafana dashboards

## Resources

- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## License

This is a portfolio project for demonstration purposes.
