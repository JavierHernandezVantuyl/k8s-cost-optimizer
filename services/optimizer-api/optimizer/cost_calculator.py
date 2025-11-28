import os
import httpx
from typing import Dict, List
from models import Workload, CostEstimate, CostBreakdown


class CostCalculator:

    def __init__(self):
        self.aws_pricing_url = os.getenv("AWS_PRICING_URL", "http://aws-pricing-api:8000")
        self.gcp_pricing_url = os.getenv("GCP_PRICING_URL", "http://gcp-pricing-api:8000")
        self.azure_pricing_url = os.getenv("AZURE_PRICING_URL", "http://azure-pricing-api:8000")
        self.client = httpx.AsyncClient(timeout=30.0)

    def _get_pricing_url(self, provider: str) -> str:
        urls = {
            "aws": self.aws_pricing_url,
            "gcp": self.gcp_pricing_url,
            "azure": self.azure_pricing_url
        }
        return urls.get(provider.lower(), self.aws_pricing_url)

    def _parse_cpu(self, cpu_string: str) -> float:
        if cpu_string.endswith('m'):
            return float(cpu_string[:-1]) / 1000
        return float(cpu_string)

    def _parse_memory(self, memory_string: str) -> int:
        multipliers = {
            'Ki': 1024,
            'Mi': 1024 * 1024,
            'Gi': 1024 * 1024 * 1024,
            'K': 1000,
            'M': 1000 * 1000,
            'G': 1000 * 1000 * 1000
        }
        for suffix, multiplier in multipliers.items():
            if memory_string.endswith(suffix):
                return int(float(memory_string[:-len(suffix)]) * multiplier)
        return int(memory_string)

    async def fetch_current_costs(self, workload: Workload, instance_type: str = None) -> CostEstimate:
        provider = workload.provider.lower()
        pricing_url = self._get_pricing_url(provider)

        if not instance_type:
            instance_type = self._infer_instance_type(workload, provider)

        cpu_cores = self._parse_cpu(workload.current_resources.cpu_request)
        memory_gb = self._parse_memory(workload.current_resources.memory_request) / (1024 ** 3)

        request_data = {
            "instance_type": instance_type,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "storage_gb": 10,
            "network_gb": 50,
            "hours": 730,
            "region": "us-east-1"
        }

        try:
            response = await self.client.post(f"{pricing_url}/pricing", json=request_data)
            response.raise_for_status()
            pricing_data = response.json()

            breakdown = CostBreakdown(
                compute=pricing_data["breakdown"]["compute"],
                memory=pricing_data["breakdown"]["memory"],
                storage=pricing_data["breakdown"]["storage"],
                network=pricing_data["breakdown"]["network"],
                total=pricing_data["breakdown"]["total"]
            )

            monthly_cost = pricing_data["monthly_cost"] * workload.replicas

            return CostEstimate(
                hourly=pricing_data["hourly_cost"] * workload.replicas,
                daily=monthly_cost / 30,
                monthly=monthly_cost,
                yearly=monthly_cost * 12,
                breakdown=breakdown
            )

        except Exception as e:
            return self._fallback_cost_estimate(workload)

    async def calculate_optimized_costs(
        self,
        workload: Workload,
        recommended_config: Dict,
        instance_type: str = None
    ) -> CostEstimate:
        provider = workload.provider.lower()
        pricing_url = self._get_pricing_url(provider)

        if not instance_type:
            instance_type = self._infer_instance_type_from_config(recommended_config, provider)

        cpu_cores = self._parse_cpu(recommended_config.get("cpu_request", workload.current_resources.cpu_request))
        memory_gb = self._parse_memory(recommended_config.get("memory_request", workload.current_resources.memory_request)) / (1024 ** 3)
        replicas = recommended_config.get("replicas", workload.replicas)

        request_data = {
            "instance_type": instance_type,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "storage_gb": 10,
            "network_gb": 50,
            "hours": 730,
            "region": "us-east-1"
        }

        try:
            response = await self.client.post(f"{pricing_url}/pricing", json=request_data)
            response.raise_for_status()
            pricing_data = response.json()

            breakdown = CostBreakdown(
                compute=pricing_data["breakdown"]["compute"],
                memory=pricing_data["breakdown"]["memory"],
                storage=pricing_data["breakdown"]["storage"],
                network=pricing_data["breakdown"]["network"],
                total=pricing_data["breakdown"]["total"]
            )

            monthly_cost = pricing_data["monthly_cost"] * replicas

            return CostEstimate(
                hourly=pricing_data["hourly_cost"] * replicas,
                daily=monthly_cost / 30,
                monthly=monthly_cost,
                yearly=monthly_cost * 12,
                breakdown=breakdown
            )

        except Exception as e:
            return self._fallback_optimized_cost_estimate(workload, recommended_config)

    async def compare_providers(self, workload: Workload, instance_type: str = None) -> Dict[str, CostEstimate]:
        results = {}

        for provider in ["aws", "gcp", "azure"]:
            temp_workload = workload.model_copy()
            temp_workload.provider = provider

            cost = await self.fetch_current_costs(temp_workload, instance_type)
            results[provider] = cost

        return results

    async def spot_vs_ondemand(self, workload: Workload, instance_type: str = None) -> Dict:
        provider = workload.provider.lower()
        pricing_url = self._get_pricing_url(provider)

        if not instance_type:
            instance_type = self._infer_instance_type(workload, provider)

        try:
            spot_response = await self.client.get(f"{pricing_url}/spot-prices")
            spot_response.raise_for_status()
            spot_data = spot_response.json()

            spot_prices = [
                p for p in spot_data.get("prices", [])
                if p["instance_type"] == instance_type
            ]

            if spot_prices:
                spot_price = spot_prices[0]
                on_demand_monthly = spot_price["on_demand_price"] * 730 * workload.replicas
                spot_monthly = spot_price["spot_price"] * 730 * workload.replicas
                savings = on_demand_monthly - spot_monthly

                return {
                    "on_demand_monthly": on_demand_monthly,
                    "spot_monthly": spot_monthly,
                    "monthly_savings": savings,
                    "savings_percentage": (savings / on_demand_monthly) * 100 if on_demand_monthly > 0 else 0,
                    "discount_percentage": spot_price["discount_percentage"],
                    "interruption_rate": spot_price.get("interruption_rate", "unknown")
                }

        except Exception as e:
            pass

        return {
            "on_demand_monthly": 0,
            "spot_monthly": 0,
            "monthly_savings": 0,
            "savings_percentage": 0,
            "discount_percentage": 0,
            "interruption_rate": "unknown"
        }

    def calculate_annual_savings(self, monthly_savings: float) -> float:
        return monthly_savings * 12

    def _infer_instance_type(self, workload: Workload, provider: str) -> str:
        cpu_cores = self._parse_cpu(workload.current_resources.cpu_request)
        memory_gb = self._parse_memory(workload.current_resources.memory_request) / (1024 ** 3)

        if provider == "aws":
            if cpu_cores <= 0.5 and memory_gb <= 1:
                return "t3.micro"
            elif cpu_cores <= 1 and memory_gb <= 2:
                return "t3.small"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "t3.medium"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "m5.large"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "m5.xlarge"
            else:
                return "m5.2xlarge"

        elif provider == "gcp":
            if cpu_cores <= 0.5 and memory_gb <= 1:
                return "e2-micro"
            elif cpu_cores <= 1 and memory_gb <= 2:
                return "e2-small"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "e2-medium"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "n2-standard-2"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "n2-standard-4"
            else:
                return "n2-standard-8"

        else:
            if cpu_cores <= 1 and memory_gb <= 1:
                return "B1s"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "B2s"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "Standard_D2s_v3"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "Standard_D4s_v3"
            else:
                return "Standard_D8s_v3"

    def _infer_instance_type_from_config(self, config: Dict, provider: str) -> str:
        cpu_cores = self._parse_cpu(config.get("cpu_request", "1000m"))
        memory_gb = self._parse_memory(config.get("memory_request", "1Gi")) / (1024 ** 3)

        if provider == "aws":
            if cpu_cores <= 0.5 and memory_gb <= 1:
                return "t3.micro"
            elif cpu_cores <= 1 and memory_gb <= 2:
                return "t3.small"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "t3.medium"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "m5.large"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "m5.xlarge"
            else:
                return "m5.2xlarge"

        elif provider == "gcp":
            if cpu_cores <= 0.5 and memory_gb <= 1:
                return "e2-micro"
            elif cpu_cores <= 1 and memory_gb <= 2:
                return "e2-small"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "e2-medium"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "n2-standard-2"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "n2-standard-4"
            else:
                return "n2-standard-8"

        else:
            if cpu_cores <= 1 and memory_gb <= 1:
                return "B1s"
            elif cpu_cores <= 2 and memory_gb <= 4:
                return "B2s"
            elif cpu_cores <= 2 and memory_gb <= 8:
                return "Standard_D2s_v3"
            elif cpu_cores <= 4 and memory_gb <= 16:
                return "Standard_D4s_v3"
            else:
                return "Standard_D8s_v3"

    def _fallback_cost_estimate(self, workload: Workload) -> CostEstimate:
        cpu_cores = self._parse_cpu(workload.current_resources.cpu_request)
        memory_gb = self._parse_memory(workload.current_resources.memory_request) / (1024 ** 3)

        hourly_cost = (cpu_cores * 0.04 + memory_gb * 0.005) * workload.replicas
        monthly_cost = hourly_cost * 730

        breakdown = CostBreakdown(
            compute=monthly_cost * 0.7,
            memory=monthly_cost * 0.2,
            storage=monthly_cost * 0.05,
            network=monthly_cost * 0.05,
            total=monthly_cost
        )

        return CostEstimate(
            hourly=hourly_cost,
            daily=monthly_cost / 30,
            monthly=monthly_cost,
            yearly=monthly_cost * 12,
            breakdown=breakdown
        )

    def _fallback_optimized_cost_estimate(self, workload: Workload, recommended_config: Dict) -> CostEstimate:
        cpu_cores = self._parse_cpu(recommended_config.get("cpu_request", workload.current_resources.cpu_request))
        memory_gb = self._parse_memory(recommended_config.get("memory_request", workload.current_resources.memory_request)) / (1024 ** 3)
        replicas = recommended_config.get("replicas", workload.replicas)

        hourly_cost = (cpu_cores * 0.04 + memory_gb * 0.005) * replicas
        monthly_cost = hourly_cost * 730

        breakdown = CostBreakdown(
            compute=monthly_cost * 0.7,
            memory=monthly_cost * 0.2,
            storage=monthly_cost * 0.05,
            network=monthly_cost * 0.05,
            total=monthly_cost
        )

        return CostEstimate(
            hourly=hourly_cost,
            daily=monthly_cost / 30,
            monthly=monthly_cost,
            yearly=monthly_cost * 12,
            breakdown=breakdown
        )

    async def close(self):
        await self.client.aclose()
