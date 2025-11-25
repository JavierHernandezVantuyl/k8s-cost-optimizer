#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service_name=$1
    local check_command=$2

    if eval "${check_command}" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${service_name}"
        return 0
    else
        echo -e "  ${RED}✗${NC} ${service_name}"
        return 1
    fi
}

check_service_with_retry() {
    local service_name=$1
    local check_command=$2
    local max_attempts=${3:-3}
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if eval "${check_command}" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} ${service_name}"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            sleep 2
        fi
    done

    echo -e "  ${RED}✗${NC} ${service_name}"
    return 1
}

echo "==> Checking Docker Services..."
echo ""

POSTGRES_HEALTHY=0
REDIS_HEALTHY=0
MINIO_HEALTHY=0
PROMETHEUS_HEALTHY=0
GRAFANA_HEALTHY=0

check_service_with_retry "PostgreSQL" \
    "docker exec k8s-optimizer-postgres pg_isready -U optimizer" && POSTGRES_HEALTHY=1

check_service_with_retry "Redis" \
    "docker exec k8s-optimizer-redis redis-cli ping | grep -q PONG" && REDIS_HEALTHY=1

check_service_with_retry "MinIO" \
    "curl -sf http://localhost:9000/minio/health/live" && MINIO_HEALTHY=1

check_service_with_retry "Prometheus" \
    "curl -sf http://localhost:9090/-/healthy" && PROMETHEUS_HEALTHY=1

check_service_with_retry "Grafana" \
    "curl -sf http://localhost:3000/api/health" && GRAFANA_HEALTHY=1

echo ""
echo "==> Checking Kind Clusters..."
echo ""

AWS_HEALTHY=0
GCP_HEALTHY=0
AZURE_HEALTHY=0

check_service "AWS Cluster" \
    "kubectl get nodes --context kind-aws-cluster" && AWS_HEALTHY=1

check_service "GCP Cluster" \
    "kubectl get nodes --context kind-gcp-cluster" && GCP_HEALTHY=1

check_service "Azure Cluster" \
    "kubectl get nodes --context kind-azure-cluster" && AZURE_HEALTHY=1

echo ""

TOTAL_SERVICES=8
HEALTHY_SERVICES=$((POSTGRES_HEALTHY + REDIS_HEALTHY + MINIO_HEALTHY + PROMETHEUS_HEALTHY + GRAFANA_HEALTHY + AWS_HEALTHY + GCP_HEALTHY + AZURE_HEALTHY))

if [ $HEALTHY_SERVICES -eq $TOTAL_SERVICES ]; then
    echo -e "${GREEN}==> All services are healthy! (${HEALTHY_SERVICES}/${TOTAL_SERVICES})${NC}"
    exit 0
elif [ $HEALTHY_SERVICES -gt 0 ]; then
    echo -e "${YELLOW}==> Some services are unhealthy (${HEALTHY_SERVICES}/${TOTAL_SERVICES})${NC}"
    exit 1
else
    echo -e "${RED}==> All services are unhealthy (${HEALTHY_SERVICES}/${TOTAL_SERVICES})${NC}"
    exit 1
fi
