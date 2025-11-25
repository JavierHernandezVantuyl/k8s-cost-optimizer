#!/usr/bin/env bash

set -euo pipefail

echo "Cleaning up Kind clusters..."

delete_cluster() {
    local cluster_name=$1

    if kind get clusters 2>/dev/null | grep -q "^${cluster_name}$"; then
        echo "  Deleting cluster: ${cluster_name}..."
        if kind delete cluster --name "${cluster_name}"; then
            echo "  ✓ Cluster ${cluster_name} deleted"
        else
            echo "  ✗ Failed to delete cluster ${cluster_name}" >&2
            return 1
        fi
    else
        echo "  ✓ Cluster ${cluster_name} does not exist"
    fi
}

echo ""
echo "==> Removing AWS Cluster"
delete_cluster "aws-cluster"

echo ""
echo "==> Removing GCP Cluster"
delete_cluster "gcp-cluster"

echo ""
echo "==> Removing Azure Cluster"
delete_cluster "azure-cluster"

echo ""
remaining_clusters=$(kind get clusters 2>/dev/null | wc -l | tr -d ' ')
if [ "${remaining_clusters}" -eq 0 ]; then
    echo "==> All clusters removed successfully!"
else
    echo "==> Cleanup complete. ${remaining_clusters} other cluster(s) remain."
fi
