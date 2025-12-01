#!/usr/bin/env bash

set -e

echo "Testing Mock Cloud Pricing APIs"
echo "================================"
echo ""

check_api() {
    local name=$1
    local port=$2
    local url="http://localhost:${port}"

    echo "Testing ${name} API on port ${port}..."

    if ! curl -sf "${url}/health" > /dev/null; then
        echo "  ✗ Health check failed"
        return 1
    fi
    echo "  ✓ Health check passed"

    if ! curl -sf "${url}/instances" > /dev/null; then
        echo "  ✗ Instances endpoint failed"
        return 1
    fi
    echo "  ✓ Instances endpoint working"

    local pricing_response=$(curl -sf -X POST "${url}/pricing" \
        -H "Content-Type: application/json" \
        -d '{"instance_type": "t3.micro", "cpu_cores": 2, "memory_gb": 1}' 2>/dev/null || echo "")

    if [ -z "$pricing_response" ]; then
        echo "  ✗ Pricing endpoint failed"
        return 1
    fi
    echo "  ✓ Pricing endpoint working"

    echo "  ✓ ${name} API is fully functional"
    echo ""
    return 0
}

AWS_OK=0
GCP_OK=0
AZURE_OK=0

check_api "AWS" 5001 && AWS_OK=1
check_api "GCP" 5002 && GCP_OK=1
check_api "Azure" 5003 && AZURE_OK=1

TOTAL=$((AWS_OK + GCP_OK + AZURE_OK))

echo "================================"
echo "Results: ${TOTAL}/3 APIs operational"
echo ""

if [ $TOTAL -eq 3 ]; then
    echo "✓ All pricing APIs are working correctly!"
    echo ""
    echo "Access the APIs:"
    echo "  AWS:   http://localhost:5001/docs"
    echo "  GCP:   http://localhost:5002/docs"
    echo "  Azure: http://localhost:5003/docs"
    exit 0
else
    echo "✗ Some APIs are not responding"
    echo ""
    echo "Make sure to start the services first:"
    echo "  docker-compose up aws-pricing-api gcp-pricing-api azure-pricing-api"
    exit 1
fi
