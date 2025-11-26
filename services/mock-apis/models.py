from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ResourceUsage(BaseModel):
    instance_type: str = Field(..., description="Instance type identifier")
    cpu_cores: float = Field(..., gt=0, description="Number of CPU cores")
    memory_gb: float = Field(..., gt=0, description="Memory in GB")
    storage_gb: float = Field(default=0, ge=0, description="Storage in GB")
    network_gb: float = Field(default=0, ge=0, description="Network egress in GB")
    hours: float = Field(default=730, gt=0, description="Hours of usage per month")
    region: str = Field(default="us-east-1", description="Cloud region")


class CostBreakdown(BaseModel):
    compute: float = Field(..., ge=0, description="Compute cost")
    memory: float = Field(..., ge=0, description="Memory cost")
    storage: float = Field(..., ge=0, description="Storage cost")
    network: float = Field(..., ge=0, description="Network cost")
    total: float = Field(..., ge=0, description="Total cost")


class PricingResponse(BaseModel):
    provider: str = Field(..., description="Cloud provider name")
    instance_type: str = Field(..., description="Instance type")
    region: str = Field(..., description="Cloud region")
    hourly_cost: float = Field(..., ge=0, description="Cost per hour")
    monthly_cost: float = Field(..., ge=0, description="Cost per month")
    yearly_cost: float = Field(..., ge=0, description="Cost per year")
    breakdown: CostBreakdown
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EstimateRequest(BaseModel):
    resources: List[ResourceUsage] = Field(..., min_length=1)
    period_months: int = Field(default=1, gt=0, le=36)


class EstimateResponse(BaseModel):
    provider: str
    total_cost: float = Field(..., ge=0)
    period_months: int
    resources_count: int
    breakdown_by_resource: List[PricingResponse]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InstanceType(BaseModel):
    name: str = Field(..., description="Instance type name")
    family: str = Field(..., description="Instance family")
    cpu_cores: int = Field(..., gt=0)
    memory_gb: float = Field(..., gt=0)
    hourly_cost: float = Field(..., ge=0)
    monthly_cost: float = Field(..., ge=0)
    storage_included_gb: int = Field(default=0, ge=0)
    network_performance: str = Field(default="moderate")
    available_regions: List[str] = Field(default_factory=list)


class OptimizationRecommendation(BaseModel):
    current_instance: str
    recommended_instance: str
    reason: str
    current_monthly_cost: float = Field(..., ge=0)
    recommended_monthly_cost: float = Field(..., ge=0)
    monthly_savings: float = Field(..., ge=0)
    yearly_savings: float = Field(..., ge=0)
    savings_percentage: float = Field(..., ge=0, le=100)
    confidence_score: float = Field(..., ge=0, le=1.0)
    implementation_complexity: str = Field(default="low")


class OptimizationRequest(BaseModel):
    current_usage: ResourceUsage
    cpu_utilization_avg: float = Field(..., ge=0, le=100)
    memory_utilization_avg: float = Field(..., ge=0, le=100)
    optimize_for: str = Field(default="cost", description="cost, performance, or balanced")


class OptimizationResponse(BaseModel):
    provider: str
    recommendations: List[OptimizationRecommendation]
    total_potential_savings: float = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SpotPrice(BaseModel):
    instance_type: str
    region: str
    availability_zone: str
    spot_price: float = Field(..., ge=0)
    on_demand_price: float = Field(..., ge=0)
    discount_percentage: float = Field(..., ge=0, le=100)
    interruption_rate: str = Field(default="low")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SpotPricesResponse(BaseModel):
    provider: str
    prices: List[SpotPrice]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str = Field(default="healthy")
    provider: str
    version: str = Field(default="1.0.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
