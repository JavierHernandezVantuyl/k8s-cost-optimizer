from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExportFormat(str, Enum):
    YAML = "yaml"
    TERRAFORM = "terraform"
    CSV = "csv"
    JSON = "json"


class OptimizationType(str, Enum):
    RIGHT_SIZE_CPU = "right_size_cpu"
    RIGHT_SIZE_MEMORY = "right_size_memory"
    REDUCE_REPLICAS = "reduce_replicas"
    INCREASE_REPLICAS = "increase_replicas"
    SPOT_INSTANCES = "spot_instances"
    CHANGE_INSTANCE_TYPE = "change_instance_type"
    CONSOLIDATE_NODES = "consolidate_nodes"
    MOVE_TO_CHEAPER_REGION = "move_to_cheaper_region"
    SCHEDULED_SCALING = "scheduled_scaling"
    REMOVE_UNUSED = "remove_unused"


class Cluster(BaseModel):
    id: str
    name: str
    provider: str
    region: str
    node_count: int


class ResourceSpec(BaseModel):
    cpu_request: str
    memory_request: str
    cpu_limit: str
    memory_limit: str


class Workload(BaseModel):
    id: str
    cluster_id: str
    cluster_name: str
    namespace: str
    name: str
    kind: str
    replicas: int
    current_resources: ResourceSpec
    provider: str


class MetricStats(BaseModel):
    avg: float
    p50: float
    p95: float
    p99: float
    max: float
    min: float


class WorkloadMetrics(BaseModel):
    workload_id: str
    cpu_usage: MetricStats
    memory_usage: MetricStats
    cpu_utilization_pct: float
    memory_utilization_pct: float
    sample_count: int
    time_range_hours: int


class CostBreakdown(BaseModel):
    compute: float = Field(ge=0)
    memory: float = Field(ge=0)
    storage: float = Field(ge=0)
    network: float = Field(ge=0)
    total: float = Field(ge=0)


class CostEstimate(BaseModel):
    hourly: float = Field(ge=0)
    daily: float = Field(ge=0)
    monthly: float = Field(ge=0)
    yearly: float = Field(ge=0)
    breakdown: CostBreakdown


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    level: RiskLevel
    score: float = Field(ge=0, le=1.0)
    factors: List[str]
    mitigation_steps: List[str]


class RollbackPlan(BaseModel):
    steps: List[str]
    estimated_time_minutes: int
    automation_available: bool


class OptimizationRecommendation(BaseModel):
    id: str
    workload_id: str
    workload_name: str
    cluster_name: str
    namespace: str
    optimization_type: OptimizationType
    title: str
    description: str
    current_config: Dict
    recommended_config: Dict
    current_cost: CostEstimate
    optimized_cost: CostEstimate
    monthly_savings: float = Field(ge=0)
    yearly_savings: float = Field(ge=0)
    savings_percentage: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1.0)
    risk_assessment: RiskAssessment
    rollback_plan: RollbackPlan
    dependencies: List[str] = []
    implementation_complexity: str
    estimated_implementation_time: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizationResult(BaseModel):
    workload: Workload
    metrics: WorkloadMetrics
    recommendations: List[OptimizationRecommendation]
    total_potential_savings: float = Field(ge=0)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClusterCostSummary(BaseModel):
    cluster_name: str
    provider: str
    workload_count: int
    current_monthly_cost: float
    optimized_monthly_cost: float
    potential_monthly_savings: float
    savings_percentage: float
    recommendation_count: int


class CostSummary(BaseModel):
    total_workloads: int
    total_current_monthly_cost: float
    total_optimized_monthly_cost: float
    total_potential_monthly_savings: float
    total_potential_yearly_savings: float
    overall_savings_percentage: float
    clusters: List[ClusterCostSummary]
    top_recommendations: List[OptimizationRecommendation]
    by_optimization_type: Dict[str, float]
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class SavingsHistory(BaseModel):
    period_start: datetime
    period_end: datetime
    total_recommendations_generated: int
    recommendations_applied: int
    potential_savings: float
    realized_savings: float
    realization_rate: float


class ApplyRecommendationRequest(BaseModel):
    dry_run: bool = False
    auto_rollback_on_failure: bool = True
    validation_timeout_seconds: int = 300


class ApplyRecommendationResponse(BaseModel):
    recommendation_id: str
    status: str
    message: str
    applied_at: Optional[datetime] = None
    rollback_plan: Optional[RollbackPlan] = None


class TerraformExport(BaseModel):
    provider: str
    resources: List[Dict]
    outputs: Dict
    terraform_version: str = "1.0"


class CSVRow(BaseModel):
    cluster: str
    namespace: str
    workload: str
    optimization_type: str
    current_monthly_cost: float
    optimized_monthly_cost: float
    monthly_savings: float
    savings_percentage: float
    confidence_score: float
    risk_level: str
    status: str


class AnalysisRequest(BaseModel):
    cluster_filter: Optional[List[str]] = None
    namespace_filter: Optional[List[str]] = None
    min_savings_threshold: float = 0.0
    min_confidence: float = 0.5
    include_high_risk: bool = False


class OptimizeWorkloadRequest(BaseModel):
    optimization_types: Optional[List[OptimizationType]] = None
    min_confidence: float = 0.6
    max_risk_level: RiskLevel = RiskLevel.MEDIUM


class WebSocketUpdate(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict
