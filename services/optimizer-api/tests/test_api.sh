#!/bin/bash

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "========================================="
echo "K8s Cost Optimizer API - Test Suite"
echo "========================================="
echo ""
echo "Testing API at: $API_URL"
echo ""

echo "1. Health Check"
echo "----------------------------------------"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

echo "2. Analyze All Workloads"
echo "----------------------------------------"
echo "POST $API_URL/analyze"
curl -s -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -d '{"min_confidence": 0.5, "include_high_risk": false}' | python3 -m json.tool | head -n 50
echo ""
echo "... (output truncated)"
echo ""
echo ""

echo "3. Get Recommendations (min \$50 savings)"
echo "----------------------------------------"
echo "GET $API_URL/recommendations?min_savings=50&min_confidence=0.7&limit=5"
curl -s "$API_URL/recommendations?min_savings=50&min_confidence=0.7&limit=5" | python3 -m json.tool
echo ""
echo ""

echo "4. Get Savings History (Last 30 Days)"
echo "----------------------------------------"
echo "GET $API_URL/savings/history?days=30"
curl -s "$API_URL/savings/history?days=30" | python3 -m json.tool
echo ""
echo ""

echo "5. Export to CSV"
echo "----------------------------------------"
echo "GET $API_URL/export/csv"
curl -s "$API_URL/export/csv" | head -n 10
echo ""
echo "... (output truncated)"
echo ""
echo ""

echo "6. Export to Terraform"
echo "----------------------------------------"
echo "POST $API_URL/export/terraform"
curl -s -X POST "$API_URL/export/terraform" | python3 -m json.tool | head -n 30
echo ""
echo "... (output truncated)"
echo ""
echo ""

echo "========================================="
echo "Test Suite Complete"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. View full analysis in Grafana: http://localhost:3000"
echo "  2. Check Prometheus metrics: http://localhost:9090"
echo "  3. Query workload details via API"
echo ""
