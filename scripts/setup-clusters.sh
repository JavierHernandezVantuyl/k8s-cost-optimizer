#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Creating Kind clusters for multi-cloud simulation..."

create_cluster() {
    local cluster_name=$1
    local config_file=$2

    if kind get clusters 2>/dev/null | grep -q "^${cluster_name}$"; then
        echo "  ✓ Cluster ${cluster_name} already exists"
        return 0
    fi

    echo "  Creating cluster: ${cluster_name}..."
    if kind create cluster --name "${cluster_name}" --config "${config_file}"; then
        echo "  ✓ Cluster ${cluster_name} created successfully"
    else
        echo "  ✗ Failed to create cluster ${cluster_name}" >&2
        return 1
    fi
}

echo ""
echo "==> AWS Cluster (3 nodes)"
create_cluster "aws-cluster" "${PROJECT_ROOT}/config/kind/aws-cluster.yaml"

echo ""
echo "==> GCP Cluster (2 nodes)"
create_cluster "gcp-cluster" "${PROJECT_ROOT}/config/kind/gcp-cluster.yaml"

echo ""
echo "==> Azure Cluster (2 nodes)"
create_cluster "azure-cluster" "${PROJECT_ROOT}/config/kind/azure-cluster.yaml"

echo ""
echo "==> Verifying clusters..."
for cluster in aws-cluster gcp-cluster azure-cluster; do
    if kubectl get nodes --context "kind-${cluster}" >/dev/null 2>&1; then
        node_count=$(kubectl get nodes --context "kind-${cluster}" --no-headers | wc -l | tr -d ' ')
        echo "  ✓ ${cluster}: ${node_count} nodes ready"
    else
        echo "  ✗ ${cluster}: failed to connect" >&2
        exit 1
    fi
done

echo ""
echo "==> All clusters created successfully!"
echo ""
echo "To interact with clusters:"
echo "  kubectl --context kind-aws-cluster get nodes"
echo "  kubectl --context kind-gcp-cluster get nodes"
echo "  kubectl --context kind-azure-cluster get nodes"
