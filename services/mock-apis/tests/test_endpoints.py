import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_check_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_has_status(self):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_has_provider(self):
        response = client.get("/health")
        data = response.json()
        assert "provider" in data
        assert data["provider"] in ["aws", "gcp", "azure"]

    def test_health_check_has_version(self):
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestInstancesEndpoint:

    def test_get_instances_returns_200(self):
        response = client.get("/instances")
        assert response.status_code == 200

    def test_get_instances_returns_list(self):
        response = client.get("/instances")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_instance_has_required_fields(self):
        response = client.get("/instances")
        data = response.json()
        instance = data[0]

        required_fields = ["name", "family", "cpu_cores", "memory_gb",
                          "hourly_cost", "monthly_cost"]
        for field in required_fields:
            assert field in instance

    def test_instance_costs_are_positive(self):
        response = client.get("/instances")
        data = response.json()

        for instance in data:
            assert instance["hourly_cost"] > 0
            assert instance["monthly_cost"] > 0

    def test_instance_monthly_cost_calculation(self):
        response = client.get("/instances")
        data = response.json()

        for instance in data:
            expected_monthly = instance["hourly_cost"] * 730
            actual_monthly = instance["monthly_cost"]
            assert abs(expected_monthly - actual_monthly) < expected_monthly * 0.2


class TestPricingEndpoint:

    def test_pricing_endpoint_returns_200(self):
        payload = {
            "instance_type": "t3.micro",
            "cpu_cores": 2,
            "memory_gb": 1,
            "storage_gb": 10,
            "network_gb": 5,
            "hours": 730,
            "region": "us-east-1"
        }
        response = client.post("/pricing", json=payload)
        assert response.status_code == 200

    def test_pricing_response_structure(self):
        payload = {
            "instance_type": "t3.micro",
            "cpu_cores": 2,
            "memory_gb": 1
        }
        response = client.post("/pricing", json=payload)
        data = response.json()

        required_fields = ["provider", "instance_type", "region",
                          "hourly_cost", "monthly_cost", "yearly_cost", "breakdown"]
        for field in required_fields:
            assert field in data

    def test_pricing_breakdown_structure(self):
        payload = {
            "instance_type": "t3.micro",
            "cpu_cores": 2,
            "memory_gb": 1
        }
        response = client.post("/pricing", json=payload)
        data = response.json()
        breakdown = data["breakdown"]

        assert "compute" in breakdown
        assert "memory" in breakdown
        assert "storage" in breakdown
        assert "network" in breakdown
        assert "total" in breakdown

    def test_pricing_with_invalid_instance(self):
        payload = {
            "instance_type": "invalid.type",
            "cpu_cores": 2,
            "memory_gb": 1
        }
        response = client.post("/pricing", json=payload)
        assert response.status_code == 404

    def test_pricing_costs_are_positive(self):
        payload = {
            "instance_type": "t3.micro",
            "cpu_cores": 2,
            "memory_gb": 1
        }
        response = client.post("/pricing", json=payload)
        data = response.json()

        assert data["hourly_cost"] >= 0
        assert data["monthly_cost"] >= 0
        assert data["yearly_cost"] >= 0


class TestEstimateEndpoint:

    def test_estimate_endpoint_returns_200(self):
        payload = {
            "resources": [
                {
                    "instance_type": "t3.micro",
                    "cpu_cores": 2,
                    "memory_gb": 1
                }
            ],
            "period_months": 1
        }
        response = client.post("/estimate", json=payload)
        assert response.status_code == 200

    def test_estimate_response_structure(self):
        payload = {
            "resources": [
                {
                    "instance_type": "t3.micro",
                    "cpu_cores": 2,
                    "memory_gb": 1
                }
            ],
            "period_months": 3
        }
        response = client.post("/estimate", json=payload)
        data = response.json()

        assert "provider" in data
        assert "total_cost" in data
        assert "period_months" in data
        assert "resources_count" in data
        assert "breakdown_by_resource" in data

    def test_estimate_multiple_resources(self):
        payload = {
            "resources": [
                {
                    "instance_type": "t3.micro",
                    "cpu_cores": 2,
                    "memory_gb": 1
                },
                {
                    "instance_type": "t3.small",
                    "cpu_cores": 2,
                    "memory_gb": 2
                }
            ],
            "period_months": 1
        }
        response = client.post("/estimate", json=payload)
        data = response.json()

        assert data["resources_count"] == 2
        assert len(data["breakdown_by_resource"]) == 2

    def test_estimate_period_multiplier(self):
        payload = {
            "resources": [
                {
                    "instance_type": "t3.micro",
                    "cpu_cores": 2,
                    "memory_gb": 1
                }
            ],
            "period_months": 1
        }
        response_1m = client.post("/estimate", json=payload)
        data_1m = response_1m.json()

        payload["period_months"] = 12
        response_12m = client.post("/estimate", json=payload)
        data_12m = response_12m.json()

        assert data_12m["total_cost"] > data_1m["total_cost"]


class TestRecommendationsEndpoint:

    def test_recommendations_endpoint_returns_200(self):
        payload = {
            "current_usage": {
                "instance_type": "t3.medium",
                "cpu_cores": 2,
                "memory_gb": 4
            },
            "cpu_utilization_avg": 25,
            "memory_utilization_avg": 30,
            "optimize_for": "cost"
        }
        response = client.post("/recommendations", json=payload)
        assert response.status_code == 200

    def test_recommendations_response_structure(self):
        payload = {
            "current_usage": {
                "instance_type": "t3.medium",
                "cpu_cores": 2,
                "memory_gb": 4
            },
            "cpu_utilization_avg": 25,
            "memory_utilization_avg": 30,
            "optimize_for": "cost"
        }
        response = client.post("/recommendations", json=payload)
        data = response.json()

        assert "provider" in data
        assert "recommendations" in data
        assert "total_potential_savings" in data

    def test_recommendations_low_utilization(self):
        payload = {
            "current_usage": {
                "instance_type": "m5.2xlarge",
                "cpu_cores": 8,
                "memory_gb": 32
            },
            "cpu_utilization_avg": 15,
            "memory_utilization_avg": 20,
            "optimize_for": "cost"
        }
        response = client.post("/recommendations", json=payload)
        data = response.json()

        assert isinstance(data["recommendations"], list)

    def test_recommendation_has_required_fields(self):
        payload = {
            "current_usage": {
                "instance_type": "t3.large",
                "cpu_cores": 2,
                "memory_gb": 8
            },
            "cpu_utilization_avg": 25,
            "memory_utilization_avg": 30,
            "optimize_for": "cost"
        }
        response = client.post("/recommendations", json=payload)
        data = response.json()

        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            required_fields = ["current_instance", "recommended_instance", "reason",
                             "current_monthly_cost", "recommended_monthly_cost",
                             "monthly_savings", "yearly_savings", "savings_percentage",
                             "confidence_score"]
            for field in required_fields:
                assert field in rec


class TestSpotPricesEndpoint:

    def test_spot_prices_endpoint_returns_200(self):
        response = client.get("/spot-prices")
        assert response.status_code == 200

    def test_spot_prices_response_structure(self):
        response = client.get("/spot-prices")
        data = response.json()

        assert "provider" in data
        assert "prices" in data
        assert isinstance(data["prices"], list)

    def test_spot_price_has_required_fields(self):
        response = client.get("/spot-prices")
        data = response.json()

        if len(data["prices"]) > 0:
            price = data["prices"][0]
            required_fields = ["instance_type", "region", "availability_zone",
                             "spot_price", "on_demand_price", "discount_percentage"]
            for field in required_fields:
                assert field in price

    def test_spot_price_discount_range(self):
        response = client.get("/spot-prices")
        data = response.json()

        for price in data["prices"]:
            assert 60 <= price["discount_percentage"] <= 90
            assert price["spot_price"] < price["on_demand_price"]

    def test_spot_price_calculation(self):
        response = client.get("/spot-prices")
        data = response.json()

        for price in data["prices"]:
            on_demand = price["on_demand_price"]
            spot = price["spot_price"]
            discount = price["discount_percentage"]

            expected_spot = on_demand * (1 - discount / 100)
            assert abs(expected_spot - spot) < 0.01
