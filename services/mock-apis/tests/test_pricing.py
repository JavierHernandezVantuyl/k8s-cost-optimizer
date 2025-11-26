import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from models import ResourceUsage, CostBreakdown
from pricing_data import AWS_PRICING, GCP_PRICING, AZURE_PRICING


class TestPricingData:

    def test_aws_pricing_structure(self):
        assert "instances" in AWS_PRICING
        assert "storage" in AWS_PRICING
        assert "network" in AWS_PRICING
        assert "regions" in AWS_PRICING

    def test_gcp_pricing_structure(self):
        assert "instances" in GCP_PRICING
        assert "storage" in GCP_PRICING
        assert "network" in GCP_PRICING
        assert "regions" in GCP_PRICING

    def test_azure_pricing_structure(self):
        assert "instances" in AZURE_PRICING
        assert "storage" in AZURE_PRICING
        assert "network" in AZURE_PRICING
        assert "regions" in AZURE_PRICING

    def test_aws_instance_types_exist(self):
        assert "t3.micro" in AWS_PRICING["instances"]
        assert "m5.large" in AWS_PRICING["instances"]
        assert "c5.xlarge" in AWS_PRICING["instances"]

    def test_gcp_instance_types_exist(self):
        assert "e2-micro" in GCP_PRICING["instances"]
        assert "n1-standard-2" in GCP_PRICING["instances"]
        assert "n2-standard-4" in GCP_PRICING["instances"]

    def test_azure_instance_types_exist(self):
        assert "B1s" in AZURE_PRICING["instances"]
        assert "Standard_D2s_v3" in AZURE_PRICING["instances"]
        assert "Standard_F4s_v2" in AZURE_PRICING["instances"]

    def test_instance_pricing_has_required_fields(self):
        instance = AWS_PRICING["instances"]["t3.micro"]
        assert "family" in instance
        assert "cpu_cores" in instance
        assert "memory_gb" in instance
        assert "hourly_cost" in instance
        assert instance["hourly_cost"] > 0

    def test_storage_pricing_positive(self):
        for key, value in AWS_PRICING["storage"].items():
            assert value > 0, f"Storage pricing for {key} should be positive"

    def test_network_pricing_positive(self):
        for key, value in AWS_PRICING["network"].items():
            assert value > 0, f"Network pricing for {key} should be positive"

    def test_regions_list_not_empty(self):
        assert len(AWS_PRICING["regions"]) > 0
        assert len(GCP_PRICING["regions"]) > 0
        assert len(AZURE_PRICING["regions"]) > 0


class TestResourceUsageModel:

    def test_valid_resource_usage(self):
        usage = ResourceUsage(
            instance_type="t3.micro",
            cpu_cores=2,
            memory_gb=1,
            storage_gb=10,
            network_gb=5,
            hours=730,
            region="us-east-1"
        )
        assert usage.instance_type == "t3.micro"
        assert usage.cpu_cores == 2
        assert usage.memory_gb == 1

    def test_default_values(self):
        usage = ResourceUsage(
            instance_type="t3.micro",
            cpu_cores=2,
            memory_gb=1
        )
        assert usage.storage_gb == 0
        assert usage.network_gb == 0
        assert usage.hours == 730
        assert usage.region == "us-east-1"

    def test_cpu_cores_must_be_positive(self):
        with pytest.raises(ValueError):
            ResourceUsage(
                instance_type="t3.micro",
                cpu_cores=0,
                memory_gb=1
            )

    def test_memory_must_be_positive(self):
        with pytest.raises(ValueError):
            ResourceUsage(
                instance_type="t3.micro",
                cpu_cores=2,
                memory_gb=-1
            )


class TestCostBreakdown:

    def test_cost_breakdown_creation(self):
        breakdown = CostBreakdown(
            compute=10.0,
            memory=2.0,
            storage=1.5,
            network=0.5,
            total=14.0
        )
        assert breakdown.compute == 10.0
        assert breakdown.total == 14.0

    def test_costs_must_be_non_negative(self):
        with pytest.raises(ValueError):
            CostBreakdown(
                compute=-10.0,
                memory=2.0,
                storage=1.5,
                network=0.5,
                total=14.0
            )


class TestPricingCalculations:

    def test_basic_compute_cost(self):
        instance = AWS_PRICING["instances"]["t3.micro"]
        hours = 730
        expected_cost = instance["hourly_cost"] * hours
        assert expected_cost > 0
        assert expected_cost < 100

    def test_monthly_vs_yearly_cost(self):
        monthly_cost = 50.0
        yearly_cost = monthly_cost * 12
        assert yearly_cost == 600.0

    def test_storage_cost_calculation(self):
        storage_gb = 100
        rate = AWS_PRICING["storage"]["gp3_per_gb"]
        storage_cost = storage_gb * rate
        assert storage_cost == 8.0

    def test_network_cost_calculation(self):
        network_gb = 1000
        rate = AWS_PRICING["network"]["egress_per_gb"]
        network_cost = network_gb * rate
        assert network_cost == 90.0


class TestPriceComparison:

    def test_aws_vs_gcp_micro_instances(self):
        aws_micro = AWS_PRICING["instances"]["t3.micro"]["hourly_cost"]
        gcp_micro = GCP_PRICING["instances"]["e2-micro"]["hourly_cost"]
        assert aws_micro > 0
        assert gcp_micro > 0

    def test_instance_families_have_different_prices(self):
        t3_micro = AWS_PRICING["instances"]["t3.micro"]["hourly_cost"]
        t3_small = AWS_PRICING["instances"]["t3.small"]["hourly_cost"]
        assert t3_small > t3_micro

    def test_larger_instances_cost_more(self):
        m5_large = AWS_PRICING["instances"]["m5.large"]["hourly_cost"]
        m5_xlarge = AWS_PRICING["instances"]["m5.xlarge"]["hourly_cost"]
        m5_2xlarge = AWS_PRICING["instances"]["m5.2xlarge"]["hourly_cost"]
        assert m5_xlarge > m5_large
        assert m5_2xlarge > m5_xlarge
