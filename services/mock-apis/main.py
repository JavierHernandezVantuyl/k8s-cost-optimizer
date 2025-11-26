import os
import random
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ResourceUsage,
    PricingResponse,
    EstimateRequest,
    EstimateResponse,
    InstanceType,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationRecommendation,
    SpotPricesResponse,
    SpotPrice,
    HealthResponse,
    CostBreakdown
)
from pricing_data import PRICING_DATA

CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "aws").lower()

if CLOUD_PROVIDER not in PRICING_DATA:
    raise ValueError(f"Invalid CLOUD_PROVIDER: {CLOUD_PROVIDER}. Must be one of: aws, gcp, azure")

PROVIDER_DATA = PRICING_DATA[CLOUD_PROVIDER]

app = FastAPI(
    title=f"{CLOUD_PROVIDER.upper()} Pricing API",
    description=f"Mock {CLOUD_PROVIDER.upper()} pricing API for cost optimization",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def apply_variance(value: float, variance_pct: float = 15.0) -> float:
    variance = random.uniform(-variance_pct / 100, variance_pct / 100)
    return round(value * (1 + variance), 4)


def calculate_cost(instance_type: str, usage: ResourceUsage) -> CostBreakdown:
    instances = PROVIDER_DATA["instances"]
    storage_rates = PROVIDER_DATA["storage"]
    network_rates = PROVIDER_DATA["network"]

    if instance_type not in instances:
        available = ", ".join(list(instances.keys())[:5]) + "..."
        raise HTTPException(
            status_code=404,
            detail=f"Instance type '{instance_type}' not found. Available types: {available}"
        )

    instance = instances[instance_type]

    compute_cost = instance["hourly_cost"] * usage.hours
    compute_cost = apply_variance(compute_cost)

    memory_cost = 0.0
    if usage.memory_gb > instance["memory_gb"]:
        extra_memory = usage.memory_gb - instance["memory_gb"]
        memory_cost = extra_memory * 0.005 * usage.hours
        memory_cost = apply_variance(memory_cost)

    storage_key = list(storage_rates.keys())[0]
    storage_cost = usage.storage_gb * storage_rates[storage_key]
    storage_cost = apply_variance(storage_cost)

    network_cost = usage.network_gb * network_rates["egress_per_gb"]
    network_cost = apply_variance(network_cost)

    total = compute_cost + memory_cost + storage_cost + network_cost

    return CostBreakdown(
        compute=round(compute_cost, 2),
        memory=round(memory_cost, 2),
        storage=round(storage_cost, 2),
        network=round(network_cost, 2),
        total=round(total, 2)
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        provider=CLOUD_PROVIDER,
        version="1.0.0"
    )


@app.get("/instances", response_model=List[InstanceType])
async def get_instances():
    instances = []
    for name, details in PROVIDER_DATA["instances"].items():
        monthly_cost = details["hourly_cost"] * 730
        instances.append(
            InstanceType(
                name=name,
                family=details["family"],
                cpu_cores=details["cpu_cores"],
                memory_gb=details["memory_gb"],
                hourly_cost=apply_variance(details["hourly_cost"]),
                monthly_cost=apply_variance(monthly_cost),
                storage_included_gb=details["storage_included_gb"],
                network_performance=details["network_performance"],
                available_regions=PROVIDER_DATA["regions"]
            )
        )
    return instances


@app.post("/pricing", response_model=PricingResponse)
async def calculate_pricing(usage: ResourceUsage):
    breakdown = calculate_cost(usage.instance_type, usage)
    hourly_cost = breakdown.total / usage.hours
    monthly_cost = breakdown.total
    yearly_cost = monthly_cost * 12

    return PricingResponse(
        provider=CLOUD_PROVIDER,
        instance_type=usage.instance_type,
        region=usage.region,
        hourly_cost=round(hourly_cost, 4),
        monthly_cost=round(monthly_cost, 2),
        yearly_cost=round(yearly_cost, 2),
        breakdown=breakdown
    )


@app.post("/estimate", response_model=EstimateResponse)
async def calculate_estimate(request: EstimateRequest):
    breakdown_list = []
    total_monthly = 0.0

    for resource in request.resources:
        breakdown = calculate_cost(resource.instance_type, resource)
        hourly_cost = breakdown.total / resource.hours
        monthly_cost = breakdown.total
        yearly_cost = monthly_cost * 12

        pricing = PricingResponse(
            provider=CLOUD_PROVIDER,
            instance_type=resource.instance_type,
            region=resource.region,
            hourly_cost=round(hourly_cost, 4),
            monthly_cost=round(monthly_cost, 2),
            yearly_cost=round(yearly_cost, 2),
            breakdown=breakdown
        )
        breakdown_list.append(pricing)
        total_monthly += monthly_cost

    total_cost = total_monthly * request.period_months

    return EstimateResponse(
        provider=CLOUD_PROVIDER,
        total_cost=round(total_cost, 2),
        period_months=request.period_months,
        resources_count=len(request.resources),
        breakdown_by_resource=breakdown_list
    )


@app.post("/recommendations", response_model=OptimizationResponse)
async def get_recommendations(request: OptimizationRequest):
    current_instance = request.current_usage.instance_type
    instances = PROVIDER_DATA["instances"]

    if current_instance not in instances:
        raise HTTPException(
            status_code=404,
            detail=f"Instance type '{current_instance}' not found"
        )

    current = instances[current_instance]
    current_breakdown = calculate_cost(current_instance, request.current_usage)
    current_monthly = current_breakdown.total

    recommendations = []

    cpu_util = request.cpu_utilization_avg
    mem_util = request.memory_utilization_avg

    if cpu_util < 30 or mem_util < 30:
        for name, details in instances.items():
            if name == current_instance:
                continue

            if details["cpu_cores"] < current["cpu_cores"] and details["memory_gb"] < current["memory_gb"]:
                test_usage = request.current_usage.model_copy()
                test_usage.instance_type = name

                rec_breakdown = calculate_cost(name, test_usage)
                rec_monthly = rec_breakdown.total

                if rec_monthly < current_monthly:
                    savings = current_monthly - rec_monthly
                    savings_pct = (savings / current_monthly) * 100

                    confidence = 0.85 if cpu_util < 20 and mem_util < 20 else 0.70

                    recommendations.append(
                        OptimizationRecommendation(
                            current_instance=current_instance,
                            recommended_instance=name,
                            reason=f"Low resource utilization detected (CPU: {cpu_util}%, Memory: {mem_util}%). Downsizing recommended.",
                            current_monthly_cost=round(current_monthly, 2),
                            recommended_monthly_cost=round(rec_monthly, 2),
                            monthly_savings=round(savings, 2),
                            yearly_savings=round(savings * 12, 2),
                            savings_percentage=round(savings_pct, 2),
                            confidence_score=confidence,
                            implementation_complexity="low"
                        )
                    )

    if cpu_util > 70 or mem_util > 70:
        for name, details in instances.items():
            if name == current_instance:
                continue

            if details["cpu_cores"] > current["cpu_cores"] and details["memory_gb"] >= current["memory_gb"]:
                test_usage = request.current_usage.model_copy()
                test_usage.instance_type = name

                rec_breakdown = calculate_cost(name, test_usage)
                rec_monthly = rec_breakdown.total

                savings = current_monthly - rec_monthly

                recommendations.append(
                    OptimizationRecommendation(
                        current_instance=current_instance,
                        recommended_instance=name,
                        reason=f"High resource utilization detected (CPU: {cpu_util}%, Memory: {mem_util}%). Upgrading for better performance.",
                        current_monthly_cost=round(current_monthly, 2),
                        recommended_monthly_cost=round(rec_monthly, 2),
                        monthly_savings=round(savings, 2),
                        yearly_savings=round(savings * 12, 2),
                        savings_percentage=round((savings / current_monthly) * 100, 2) if current_monthly > 0 else 0,
                        confidence_score=0.75,
                        implementation_complexity="medium"
                    )
                )
                break

    if request.optimize_for == "cost" and cpu_util < 50:
        for name, details in instances.items():
            if "micro" in name or "small" in name or name.startswith("e2") or name.startswith("B"):
                if name == current_instance:
                    continue

                test_usage = request.current_usage.model_copy()
                test_usage.instance_type = name

                try:
                    rec_breakdown = calculate_cost(name, test_usage)
                    rec_monthly = rec_breakdown.total

                    if rec_monthly < current_monthly:
                        savings = current_monthly - rec_monthly
                        savings_pct = (savings / current_monthly) * 100

                        recommendations.append(
                            OptimizationRecommendation(
                                current_instance=current_instance,
                                recommended_instance=name,
                                reason="Cost optimization: switching to budget-friendly instance type.",
                                current_monthly_cost=round(current_monthly, 2),
                                recommended_monthly_cost=round(rec_monthly, 2),
                                monthly_savings=round(savings, 2),
                                yearly_savings=round(savings * 12, 2),
                                savings_percentage=round(savings_pct, 2),
                                confidence_score=0.65,
                                implementation_complexity="low"
                            )
                        )
                except:
                    pass

    recommendations.sort(key=lambda x: x.monthly_savings, reverse=True)
    recommendations = recommendations[:5]

    total_savings = sum(r.monthly_savings for r in recommendations)

    return OptimizationResponse(
        provider=CLOUD_PROVIDER,
        recommendations=recommendations,
        total_potential_savings=round(total_savings, 2)
    )


@app.get("/spot-prices", response_model=SpotPricesResponse)
async def get_spot_prices():
    instances = PROVIDER_DATA["instances"]
    regions = PROVIDER_DATA["regions"]

    prices = []

    for instance_name, instance_details in instances.items():
        for region in regions[:2]:
            zones = [f"{region}a", f"{region}b", f"{region}c"]

            for zone in zones[:2]:
                on_demand = instance_details["hourly_cost"]
                discount = random.uniform(60, 90)
                spot = on_demand * (1 - discount / 100)

                interruption_rates = ["low", "low", "moderate", "high"]
                interruption = random.choice(interruption_rates)

                prices.append(
                    SpotPrice(
                        instance_type=instance_name,
                        region=region,
                        availability_zone=zone,
                        spot_price=round(spot, 4),
                        on_demand_price=round(on_demand, 4),
                        discount_percentage=round(discount, 2),
                        interruption_rate=interruption
                    )
                )

    return SpotPricesResponse(
        provider=CLOUD_PROVIDER,
        prices=prices
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
