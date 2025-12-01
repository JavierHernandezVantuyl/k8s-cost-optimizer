#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "K8s Cost Optimizer Operator - Deployment"
echo "========================================="
echo ""

CLUSTER_NAME=${1:-"aws-cluster"}

echo "Target Cluster: $CLUSTER_NAME"
echo ""

if ! kubectl cluster-info --context kind-$CLUSTER_NAME &> /dev/null; then
    echo "Error: Cluster 'kind-$CLUSTER_NAME' not found or not accessible"
    echo "Available contexts:"
    kubectl config get-contexts
    exit 1
fi

echo "Using cluster context: kind-$CLUSTER_NAME"
kubectl config use-context kind-$CLUSTER_NAME
echo ""

echo "==> Step 1: Building Docker Image"
docker build -t cost-optimizer-operator:latest .
echo ""

echo "==> Step 2: Loading Image into Kind Cluster"
kind load docker-image cost-optimizer-operator:latest --name $CLUSTER_NAME
echo ""

echo "==> Step 3: Installing CRD"
kubectl apply -f crds/costoptimization-crd.yaml
echo "Waiting for CRD to be established..."
sleep 5
echo ""

echo "==> Step 4: Creating Namespace and RBAC"
kubectl apply -f manifests/operator/operator-rbac.yaml
echo ""

echo "==> Step 5: Deploying Operator"
kubectl apply -f manifests/operator/operator-deployment.yaml
echo ""

echo "==> Step 6: Waiting for Operator to be Ready"
kubectl wait --for=condition=available --timeout=120s deployment/cost-optimizer-operator -n cost-optimizer
echo ""

echo "==> Step 7: Verifying Installation"
echo ""
echo "Operator Pods:"
kubectl get pods -n cost-optimizer
echo ""
echo "CostOptimization CRD:"
kubectl get crd costoptimizations.optimization.k8s.io
echo ""

echo "==> Deployment Complete!"
echo ""
echo "View operator logs:"
echo "  kubectl logs -n cost-optimizer -l app=cost-optimizer-operator -f"
echo ""
echo "Check Prometheus metrics:"
echo "  kubectl port-forward -n cost-optimizer svc/cost-optimizer-operator 8080:8080"
echo "  curl http://localhost:8080/metrics"
echo ""
echo "Deploy test workloads:"
echo "  kubectl apply -f manifests/examples/test-workloads.yaml"
echo ""
echo "Apply example optimization:"
echo "  kubectl apply -f manifests/examples/cpu-optimization.yaml"
echo "  kubectl get costopt -w"
echo ""
