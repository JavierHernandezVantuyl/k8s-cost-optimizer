# Mock Cloud Pricing APIs

Mock pricing APIs simulating AWS, GCP, and Azure pricing services for local development and testing.

## Overview

This service provides realistic cloud pricing simulation without requiring actual cloud API access. Each cloud provider runs as a separate container with different pricing models and instance types.

## Features

- **Multi-cloud Support**: AWS, GCP, and Azure pricing models
- **Realistic Pricing**: Based on actual cloud provider pricing structures
- **Random Variance**: 10-20% variance to simulate real-world price fluctuations
- **Complete API**: Pricing calculations, estimates, recommendations, and spot pricing
- **Fully Tested**: Comprehensive unit and integration tests

## Endpoints

### Health Check
```
GET /health
```

### List Instance Types
```
GET /instances
```

Returns all available instance types with pricing information.

### Calculate Pricing
```
POST /pricing
```

Calculate cost for specific resource usage.

**Request Body:**
```json
{
  "instance_type": "t3.micro",
  "cpu_cores": 2,
  "memory_gb": 1,
  "storage_gb": 10,
  "network_gb": 5,
  "hours": 730,
  "region": "us-east-1"
}
```

### Cost Estimate
```
POST /estimate
```

Calculate total cost for multiple resources over a period.

**Request Body:**
```json
{
  "resources": [
    {
      "instance_type": "t3.micro",
      "cpu_cores": 2,
      "memory_gb": 1
    }
  ],
  "period_months": 12
}
```

### Optimization Recommendations
```
POST /recommendations
```

Get cost optimization suggestions based on utilization.

**Request Body:**
```json
{
  "current_usage": {
    "instance_type": "t3.large",
    "cpu_cores": 2,
    "memory_gb": 8
  },
  "cpu_utilization_avg": 25,
  "memory_utilization_avg": 30,
  "optimize_for": "cost"
}
```

### Spot Prices
```
GET /spot-prices
```

Get simulated spot instance pricing (60-90% discount).

## Running the Services

### Using Docker Compose

Start all three pricing APIs:
```bash
docker-compose up aws-pricing-api gcp-pricing-api azure-pricing-api
```

Start individual services:
```bash
docker-compose up aws-pricing-api
docker-compose up gcp-pricing-api
docker-compose up azure-pricing-api
```

### Access the APIs

- AWS Pricing API: http://localhost:5001/docs
- GCP Pricing API: http://localhost:5002/docs
- Azure Pricing API: http://localhost:5003/docs

### Local Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Run locally:
```bash
# AWS pricing API
CLOUD_PROVIDER=aws PORT=5001 python main.py

# GCP pricing API
CLOUD_PROVIDER=gcp PORT=5002 python main.py

# Azure pricing API
CLOUD_PROVIDER=azure PORT=5003 python main.py
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
pytest tests/test_pricing.py -v
pytest tests/test_endpoints.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## Pricing Data

### AWS Instance Types
- **t3 family**: t3.micro, t3.small, t3.medium, t3.large
- **m5 family**: m5.large, m5.xlarge, m5.2xlarge
- **c5 family**: c5.large, c5.xlarge, c5.2xlarge

### GCP Instance Types
- **e2 family**: e2-micro, e2-small, e2-medium
- **n1 family**: n1-standard-1, n1-standard-2, n1-standard-4
- **n2 family**: n2-standard-2, n2-standard-4, n2-standard-8

### Azure Instance Types
- **B series**: B1s, B2s, B2ms
- **D series**: Standard_D2s_v3, Standard_D4s_v3, Standard_D8s_v3
- **F series**: Standard_F2s_v2, Standard_F4s_v2, Standard_F8s_v2

## Architecture

```
mock-apis/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── pricing_data.py      # Pricing constants
├── Dockerfile           # Multi-stage build
├── requirements.txt     # Python dependencies
└── tests/
    ├── test_pricing.py      # Unit tests
    └── test_endpoints.py    # API tests
```

## Environment Variables

- `CLOUD_PROVIDER`: Cloud provider name (aws, gcp, azure)
- `PORT`: API port (default: 8000)

## Example Usage

### Calculate AWS Pricing
```bash
curl -X POST http://localhost:5001/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "instance_type": "t3.micro",
    "cpu_cores": 2,
    "memory_gb": 1,
    "storage_gb": 10,
    "network_gb": 5
  }'
```

### Compare Pricing Across Providers
```bash
# AWS
curl http://localhost:5001/instances | jq '.[] | select(.name == "t3.micro")'

# GCP
curl http://localhost:5002/instances | jq '.[] | select(.name == "e2-micro")'

# Azure
curl http://localhost:5003/instances | jq '.[] | select(.name == "B1s")'
```

### Get Optimization Recommendations
```bash
curl -X POST http://localhost:5001/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "current_usage": {
      "instance_type": "m5.2xlarge",
      "cpu_cores": 8,
      "memory_gb": 32
    },
    "cpu_utilization_avg": 15,
    "memory_utilization_avg": 20,
    "optimize_for": "cost"
  }'
```

## Notes

- Prices include 10-20% random variance to simulate real-world fluctuations
- Spot prices offer 60-90% discounts with varying interruption rates
- All costs are in USD
- Storage pricing is per month
- Network pricing is per GB egress
