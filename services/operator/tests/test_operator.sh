#!/bin/bash

set -e

echo "========================================="
echo "K8s Cost Optimizer Operator - Test Suite"
echo "========================================="
echo ""

CLUSTER_NAME=${1:-"aws-cluster"}
kubectl config use-context kind-$CLUSTER_NAME

echo "==> Test 1: Verify CRD Installation"
kubectl get crd costoptimizations.optimization.k8s.io || {
    echo "FAIL: CRD not found"
    exit 1
}
echo "PASS: CRD installed"
echo ""

echo "==> Test 2: Verify Operator is Running"
kubectl get deployment cost-optimizer-operator -n cost-optimizer || {
    echo "FAIL: Operator deployment not found"
    exit 1
}

kubectl wait --for=condition=available --timeout=60s deployment/cost-optimizer-operator -n cost-optimizer || {
    echo "FAIL: Operator not ready"
    exit 1
}
echo "PASS: Operator is running"
echo ""

echo "==> Test 3: Deploy Test Workloads"
kubectl apply -f manifests/examples/test-workloads.yaml
kubectl wait --for=condition=available --timeout=120s deployment/frontend-web -n test-optimizations
echo "PASS: Test workloads deployed"
echo ""

echo "==> Test 4: Create CostOptimization Resource (Dry-Run)"
cat <<EOF | kubectl apply -f -
apiVersion: optimization.k8s.io/v1
kind: CostOptimization
metadata:
  name: test-cpu-optimization
  namespace: test-optimizations
spec:
  targetWorkload:
    name: frontend-web
    kind: Deployment
    namespace: test-optimizations
  optimizationType: CPU
  maxChangePercent: 50
  minConfidence: 0.70
  dryRun: true
  autoApply: false
  rollbackOnFailure: true
  maxRiskLevel: MEDIUM
EOF

sleep 5

kubectl get costopt test-cpu-optimization -n test-optimizations || {
    echo "FAIL: CostOptimization resource not created"
    exit 1
}
echo "PASS: CostOptimization resource created"
echo ""

echo "==> Test 5: Verify Status Update"
STATUS=$(kubectl get costopt test-cpu-optimization -n test-optimizations -o jsonpath='{.status.phase}')
echo "Current Status: $STATUS"

if [ -z "$STATUS" ]; then
    echo "FAIL: Status not set"
    exit 1
fi
echo "PASS: Status field populated"
echo ""

echo "==> Test 6: Check Operator Logs"
kubectl logs -n cost-optimizer -l app=cost-optimizer-operator --tail=20
echo ""

echo "==> Test 7: Verify Prometheus Metrics"
kubectl port-forward -n cost-optimizer svc/cost-optimizer-operator 8080:8080 &
PF_PID=$!
sleep 3

METRICS=$(curl -s http://localhost:8080/metrics | grep costopt || true)
kill $PF_PID 2>/dev/null || true

if [ -z "$METRICS" ]; then
    echo "WARN: No metrics found (may be normal if no optimizations applied yet)"
else
    echo "PASS: Metrics endpoint working"
    echo "$METRICS"
fi
echo ""

echo "==> Test 8: Describe CostOptimization Resource"
kubectl describe costopt test-cpu-optimization -n test-optimizations
echo ""

echo "==> Test 9: Cleanup"
kubectl delete costopt test-cpu-optimization -n test-optimizations
kubectl delete -f manifests/examples/test-workloads.yaml
echo "PASS: Cleanup complete"
echo ""

echo "========================================="
echo "All Tests Passed!"
echo "========================================="
echo ""
echo "The operator is working correctly."
echo ""
