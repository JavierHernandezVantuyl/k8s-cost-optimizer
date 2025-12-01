import uuid
from typing import List, Dict
from models import (
    Workload, WorkloadMetrics, OptimizationRecommendation, OptimizationType,
    RiskAssessment, RiskLevel, RollbackPlan, ResourceSpec
)
from optimizer.ml_engine import MLEngine
from optimizer.cost_calculator import CostCalculator


class Recommender:

    def __init__(self, ml_engine: MLEngine, cost_calculator: CostCalculator):
        self.ml_engine = ml_engine
        self.cost_calculator = cost_calculator

    async def generate_recommendations(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        min_confidence: float = 0.5
    ) -> List[OptimizationRecommendation]:
        recommendations = []

        current_cost = await self.cost_calculator.fetch_current_costs(workload)

        if self.ml_engine.detect_unused_resources(metrics, threshold_pct=5.0):
            rec = await self._create_unused_resource_recommendation(workload, metrics, current_cost)
            if rec and rec.confidence_score >= min_confidence:
                recommendations.append(rec)

        right_size_rec = await self._create_right_sizing_recommendation(workload, metrics, current_cost)
        if right_size_rec and right_size_rec.confidence_score >= min_confidence:
            recommendations.append(right_size_rec)

        replica_rec = await self._create_replica_optimization_recommendation(workload, metrics, current_cost)
        if replica_rec and replica_rec.confidence_score >= min_confidence:
            recommendations.append(replica_rec)

        spot_rec = await self._create_spot_instance_recommendation(workload, metrics, current_cost)
        if spot_rec and spot_rec.confidence_score >= min_confidence:
            recommendations.append(spot_rec)

        scaling_rec = await self._create_scheduled_scaling_recommendation(workload, metrics, current_cost)
        if scaling_rec and scaling_rec.confidence_score >= min_confidence:
            recommendations.append(scaling_rec)

        recommendations.sort(key=lambda r: r.monthly_savings, reverse=True)

        return recommendations

    async def _create_right_sizing_recommendation(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        current_cost
    ) -> OptimizationRecommendation:
        new_resources, confidence = self.ml_engine.right_size_resources(workload, metrics)

        if new_resources == workload.current_resources:
            return None

        recommended_config = {
            "cpu_request": new_resources.cpu_request,
            "memory_request": new_resources.memory_request,
            "cpu_limit": new_resources.cpu_limit,
            "memory_limit": new_resources.memory_limit,
            "replicas": workload.replicas
        }

        optimized_cost = await self.cost_calculator.calculate_optimized_costs(
            workload, recommended_config
        )

        savings = current_cost.monthly - optimized_cost.monthly
        if savings <= 0:
            return None

        risk = self.assess_risk(workload, OptimizationType.RIGHT_SIZE_CPU, metrics)
        rollback = self.create_rollback_plan(workload, OptimizationType.RIGHT_SIZE_CPU)

        return OptimizationRecommendation(
            id=str(uuid.uuid4()),
            workload_id=workload.id,
            workload_name=workload.name,
            cluster_name=workload.cluster_name,
            namespace=workload.namespace,
            optimization_type=OptimizationType.RIGHT_SIZE_CPU,
            title=f"Right-size resources for {workload.name}",
            description=f"Reduce resource requests based on P95 utilization (CPU: {metrics.cpu_utilization_pct:.1f}%, Memory: {metrics.memory_utilization_pct:.1f}%)",
            current_config=workload.current_resources.dict(),
            recommended_config=recommended_config,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            monthly_savings=savings,
            yearly_savings=savings * 12,
            savings_percentage=(savings / current_cost.monthly * 100) if current_cost.monthly > 0 else 0,
            confidence_score=confidence,
            risk_assessment=risk,
            rollback_plan=rollback,
            dependencies=[],
            implementation_complexity="low",
            estimated_implementation_time="5-10 minutes"
        )

    async def _create_replica_optimization_recommendation(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        current_cost
    ) -> OptimizationRecommendation:
        recommended_replicas, confidence = self.ml_engine.optimize_replicas(workload, metrics)

        if recommended_replicas == workload.replicas:
            return None

        recommended_config = {
            **workload.current_resources.dict(),
            "replicas": recommended_replicas
        }

        optimized_cost = await self.cost_calculator.calculate_optimized_costs(
            workload, recommended_config
        )

        savings = current_cost.monthly - optimized_cost.monthly
        if savings <= 0:
            return None

        opt_type = OptimizationType.REDUCE_REPLICAS if recommended_replicas < workload.replicas else OptimizationType.INCREASE_REPLICAS
        risk = self.assess_risk(workload, opt_type, metrics)
        rollback = self.create_rollback_plan(workload, opt_type)

        return OptimizationRecommendation(
            id=str(uuid.uuid4()),
            workload_id=workload.id,
            workload_name=workload.name,
            cluster_name=workload.cluster_name,
            namespace=workload.namespace,
            optimization_type=opt_type,
            title=f"Optimize replica count for {workload.name}",
            description=f"Adjust replicas from {workload.replicas} to {recommended_replicas} based on utilization patterns",
            current_config={"replicas": workload.replicas, **workload.current_resources.dict()},
            recommended_config=recommended_config,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            monthly_savings=savings,
            yearly_savings=savings * 12,
            savings_percentage=(savings / current_cost.monthly * 100) if current_cost.monthly > 0 else 0,
            confidence_score=confidence,
            risk_assessment=risk,
            rollback_plan=rollback,
            dependencies=[],
            implementation_complexity="low",
            estimated_implementation_time="2-5 minutes"
        )

    async def _create_spot_instance_recommendation(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        current_cost
    ) -> OptimizationRecommendation:
        is_suitable, confidence, reason = self.ml_engine.recommend_spot_instances(workload, metrics)

        if not is_suitable:
            return None

        spot_data = await self.cost_calculator.spot_vs_ondemand(workload)
        savings = spot_data.get("monthly_savings", 0)

        if savings <= 0:
            return None

        recommended_config = {
            **workload.current_resources.dict(),
            "instance_type": "spot",
            "replicas": workload.replicas
        }

        optimized_cost = current_cost.model_copy()
        optimized_cost.monthly = spot_data.get("spot_monthly", current_cost.monthly)
        optimized_cost.yearly = optimized_cost.monthly * 12

        risk = RiskAssessment(
            level=RiskLevel.MEDIUM,
            score=0.5,
            factors=["Potential spot instance interruptions", "Requires fault-tolerant application design"],
            mitigation_steps=["Ensure replicas > 1", "Implement graceful shutdown", "Use spot instance pools"]
        )

        rollback = RollbackPlan(
            steps=["Scale back to on-demand instances", "Verify application stability"],
            estimated_time_minutes=5,
            automation_available=True
        )

        return OptimizationRecommendation(
            id=str(uuid.uuid4()),
            workload_id=workload.id,
            workload_name=workload.name,
            cluster_name=workload.cluster_name,
            namespace=workload.namespace,
            optimization_type=OptimizationType.SPOT_INSTANCES,
            title=f"Use spot instances for {workload.name}",
            description=f"Switch to spot instances for {spot_data.get('discount_percentage', 0):.0f}% savings. {reason}",
            current_config={"instance_type": "on-demand", **workload.current_resources.dict()},
            recommended_config=recommended_config,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            monthly_savings=savings,
            yearly_savings=savings * 12,
            savings_percentage=(savings / current_cost.monthly * 100) if current_cost.monthly > 0 else 0,
            confidence_score=confidence,
            risk_assessment=risk,
            rollback_plan=rollback,
            dependencies=[],
            implementation_complexity="medium",
            estimated_implementation_time="15-30 minutes"
        )

    async def _create_scheduled_scaling_recommendation(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        current_cost
    ) -> OptimizationRecommendation:
        scaling_opportunity = self.ml_engine.detect_scheduled_scaling_opportunity(metrics)

        if not scaling_opportunity.get("suitable", False):
            return None

        scale_down_factor = scaling_opportunity.get("off_peak_scale_down", 0.5)
        estimated_savings = current_cost.monthly * (1 - scale_down_factor) * 0.5

        if estimated_savings <= 0:
            return None

        recommended_config = {
            **workload.current_resources.dict(),
            "scaling_schedule": scaling_opportunity.get("strategy"),
            "peak_replicas": workload.replicas,
            "off_peak_replicas": max(1, int(workload.replicas * scale_down_factor))
        }

        optimized_cost = current_cost.model_copy()
        optimized_cost.monthly = current_cost.monthly - estimated_savings
        optimized_cost.yearly = optimized_cost.monthly * 12

        risk = self.assess_risk(workload, OptimizationType.SCHEDULED_SCALING, metrics)
        rollback = self.create_rollback_plan(workload, OptimizationType.SCHEDULED_SCALING)

        return OptimizationRecommendation(
            id=str(uuid.uuid4()),
            workload_id=workload.id,
            workload_name=workload.name,
            cluster_name=workload.cluster_name,
            namespace=workload.namespace,
            optimization_type=OptimizationType.SCHEDULED_SCALING,
            title=f"Implement scheduled scaling for {workload.name}",
            description=f"Scale down during off-peak hours ({scaling_opportunity.get('peak_hours', 'identified periods')})",
            current_config={"replicas": workload.replicas, "scaling": "none"},
            recommended_config=recommended_config,
            current_cost=current_cost,
            optimized_cost=optimized_cost,
            monthly_savings=estimated_savings,
            yearly_savings=estimated_savings * 12,
            savings_percentage=(estimated_savings / current_cost.monthly * 100) if current_cost.monthly > 0 else 0,
            confidence_score=scaling_opportunity.get("confidence", 0.7),
            risk_assessment=risk,
            rollback_plan=rollback,
            dependencies=[],
            implementation_complexity="medium",
            estimated_implementation_time="20-40 minutes"
        )

    async def _create_unused_resource_recommendation(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        current_cost
    ) -> OptimizationRecommendation:
        risk = RiskAssessment(
            level=RiskLevel.LOW,
            score=0.2,
            factors=["Very low resource utilization detected", "Workload may be unused"],
            mitigation_steps=["Verify workload purpose", "Check application logs", "Coordinate with team"]
        )

        rollback = RollbackPlan(
            steps=["Restore from backup", "Redeploy from manifest"],
            estimated_time_minutes=10,
            automation_available=True
        )

        return OptimizationRecommendation(
            id=str(uuid.uuid4()),
            workload_id=workload.id,
            workload_name=workload.name,
            cluster_name=workload.cluster_name,
            namespace=workload.namespace,
            optimization_type=OptimizationType.REMOVE_UNUSED,
            title=f"Remove unused workload {workload.name}",
            description=f"Workload has very low utilization (CPU: {metrics.cpu_utilization_pct:.1f}%, Memory: {metrics.memory_utilization_pct:.1f}%) and may be unused",
            current_config=workload.current_resources.dict(),
            recommended_config={"action": "delete"},
            current_cost=current_cost,
            optimized_cost=current_cost.model_copy(update={"monthly": 0, "yearly": 0}),
            monthly_savings=current_cost.monthly,
            yearly_savings=current_cost.yearly,
            savings_percentage=100.0,
            confidence_score=0.6,
            risk_assessment=risk,
            rollback_plan=rollback,
            dependencies=[],
            implementation_complexity="low",
            estimated_implementation_time="5 minutes"
        )

    def assess_risk(
        self,
        workload: Workload,
        optimization_type: OptimizationType,
        metrics: WorkloadMetrics = None
    ) -> RiskAssessment:
        risk_score = 0.3
        factors = []
        mitigation_steps = []

        if workload.kind == "StatefulSet":
            risk_score += 0.2
            factors.append("StatefulSet requires careful handling")
            mitigation_steps.append("Test in staging environment first")

        if workload.replicas == 1:
            risk_score += 0.15
            factors.append("Single replica - no redundancy")
            mitigation_steps.append("Consider increasing replicas before optimization")

        if optimization_type in [OptimizationType.REDUCE_REPLICAS, OptimizationType.RIGHT_SIZE_CPU]:
            if metrics and metrics.cpu_utilization_pct > 80:
                risk_score += 0.2
                factors.append("High CPU utilization")
                mitigation_steps.append("Monitor performance closely after change")

        if optimization_type == OptimizationType.SPOT_INSTANCES:
            risk_score = 0.5
            factors.append("Spot instances can be interrupted")
            mitigation_steps.extend([
                "Ensure application handles interruptions gracefully",
                "Maintain on-demand fallback capacity"
            ])

        if risk_score >= 0.7:
            level = RiskLevel.HIGH
        elif risk_score >= 0.5:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskAssessment(
            level=level,
            score=min(1.0, risk_score),
            factors=factors if factors else ["Standard optimization"],
            mitigation_steps=mitigation_steps if mitigation_steps else ["Follow standard deployment procedures"]
        )

    def create_rollback_plan(
        self,
        workload: Workload,
        optimization_type: OptimizationType
    ) -> RollbackPlan:
        steps = []
        estimated_time = 5

        if optimization_type in [OptimizationType.RIGHT_SIZE_CPU, OptimizationType.RIGHT_SIZE_MEMORY]:
            steps = [
                f"Restore original resource requests: {workload.current_resources.cpu_request} CPU, {workload.current_resources.memory_request} memory",
                "Apply updated manifest",
                "Verify pod stability"
            ]
            estimated_time = 5

        elif optimization_type in [OptimizationType.REDUCE_REPLICAS, OptimizationType.INCREASE_REPLICAS]:
            steps = [
                f"Scale back to {workload.replicas} replicas",
                "Verify all pods are running"
            ]
            estimated_time = 2

        elif optimization_type == OptimizationType.SPOT_INSTANCES:
            steps = [
                "Switch back to on-demand instances",
                "Verify application availability",
                "Monitor for stability"
            ]
            estimated_time = 10

        elif optimization_type == OptimizationType.SCHEDULED_SCALING:
            steps = [
                "Remove HorizontalPodAutoscaler or CronJob",
                f"Set replicas to constant {workload.replicas}"
            ]
            estimated_time = 5

        else:
            steps = ["Revert to previous configuration", "Verify workload health"]
            estimated_time = 5

        return RollbackPlan(
            steps=steps,
            estimated_time_minutes=estimated_time,
            automation_available=True
        )

    def validate_dependencies(self, workload: Workload) -> List[str]:
        dependencies = []

        if "database" in workload.name.lower() or "db" in workload.name.lower():
            dependencies.append("May have dependent applications")

        if "api" in workload.name.lower() or "gateway" in workload.name.lower():
            dependencies.append("May be a critical path component")

        if workload.kind == "DaemonSet":
            dependencies.append("Runs on all nodes - cluster-wide impact")

        return dependencies
