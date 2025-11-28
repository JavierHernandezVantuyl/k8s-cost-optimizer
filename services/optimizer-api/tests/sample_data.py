"""
Sample optimization scenarios demonstrating 35-40% cost reduction

This module contains test data showing realistic optimization scenarios
across different workload types and optimization strategies.
"""

# Scenario 1: Over-provisioned web service
OVERPROVISIONED_WEB_SERVICE = {
    "name": "frontend-web",
    "current_config": {
        "cpu_request": "2000m",
        "memory_request": "4Gi",
        "cpu_limit": "4000m",
        "memory_limit": "8Gi",
        "replicas": 5
    },
    "actual_usage": {
        "cpu_avg": "400m",
        "cpu_p95": "600m",
        "memory_avg": "1.2Gi",
        "memory_p95": "1.8Gi",
        "cpu_utilization_pct": 20.0,
        "memory_utilization_pct": 30.0
    },
    "recommended_config": {
        "cpu_request": "750m",
        "memory_request": "2Gi",
        "cpu_limit": "1500m",
        "memory_limit": "4Gi",
        "replicas": 5
    },
    "cost_reduction": {
        "current_monthly": 876.00,
        "optimized_monthly": 438.00,
        "savings": 438.00,
        "savings_percentage": 50.0
    },
    "optimization_types": ["right_size_cpu", "right_size_memory"],
    "confidence_score": 0.92
}

# Scenario 2: Excessive replica count
EXCESSIVE_REPLICAS = {
    "name": "api-gateway",
    "current_config": {
        "cpu_request": "1000m",
        "memory_request": "2Gi",
        "replicas": 8
    },
    "actual_usage": {
        "cpu_avg": "700m",
        "cpu_p95": "850m",
        "memory_avg": "1.5Gi",
        "memory_p95": "1.7Gi",
        "cpu_utilization_pct": 70.0,
        "memory_utilization_pct": 75.0
    },
    "recommended_config": {
        "cpu_request": "1000m",
        "memory_request": "2Gi",
        "replicas": 5
    },
    "cost_reduction": {
        "current_monthly": 1168.00,
        "optimized_monthly": 730.00,
        "savings": 438.00,
        "savings_percentage": 37.5
    },
    "optimization_types": ["reduce_replicas"],
    "confidence_score": 0.88
}

# Scenario 3: Spot instance candidate
SPOT_INSTANCE_CANDIDATE = {
    "name": "batch-processor",
    "current_config": {
        "instance_type": "on-demand",
        "cpu_request": "4000m",
        "memory_request": "8Gi",
        "replicas": 10
    },
    "recommended_config": {
        "instance_type": "spot",
        "cpu_request": "4000m",
        "memory_request": "8Gi",
        "replicas": 10
    },
    "cost_reduction": {
        "current_monthly": 2920.00,
        "optimized_monthly": 876.00,
        "savings": 2044.00,
        "savings_percentage": 70.0
    },
    "optimization_types": ["spot_instances"],
    "confidence_score": 0.85,
    "risk_level": "medium"
}

# Scenario 4: Unused development environment
UNUSED_DEV_ENV = {
    "name": "dev-testing-env",
    "current_config": {
        "cpu_request": "2000m",
        "memory_request": "4Gi",
        "replicas": 3
    },
    "actual_usage": {
        "cpu_avg": "50m",
        "cpu_p95": "100m",
        "memory_avg": "200Mi",
        "memory_p95": "300Mi",
        "cpu_utilization_pct": 2.5,
        "memory_utilization_pct": 7.5
    },
    "recommended_config": {
        "action": "delete"
    },
    "cost_reduction": {
        "current_monthly": 657.00,
        "optimized_monthly": 0.00,
        "savings": 657.00,
        "savings_percentage": 100.0
    },
    "optimization_types": ["remove_unused"],
    "confidence_score": 0.78
}

# Scenario 5: Scheduled scaling opportunity
SCHEDULED_SCALING_OPPORTUNITY = {
    "name": "microservice-analytics",
    "current_config": {
        "cpu_request": "500m",
        "memory_request": "1Gi",
        "replicas": 6,
        "scaling": "none"
    },
    "usage_pattern": "business_hours",
    "recommended_config": {
        "cpu_request": "500m",
        "memory_request": "1Gi",
        "peak_replicas": 6,
        "off_peak_replicas": 2,
        "scaling": "scheduled"
    },
    "cost_reduction": {
        "current_monthly": 438.00,
        "optimized_monthly": 263.00,
        "savings": 175.00,
        "savings_percentage": 40.0
    },
    "optimization_types": ["scheduled_scaling"],
    "confidence_score": 0.82
}

# Scenario 6: Wrong instance type
WRONG_INSTANCE_TYPE = {
    "name": "memory-intensive-db",
    "current_config": {
        "instance_type": "c5.2xlarge",  # Compute-optimized
        "cpu_request": "8000m",
        "memory_request": "16Gi"
    },
    "actual_usage": {
        "cpu_avg": "2000m",
        "cpu_p95": "3000m",
        "memory_avg": "14Gi",
        "memory_p95": "15.5Gi",
        "cpu_utilization_pct": 25.0,
        "memory_utilization_pct": 87.5
    },
    "recommended_config": {
        "instance_type": "r5.xlarge",  # Memory-optimized
        "cpu_request": "4000m",
        "memory_request": "16Gi"
    },
    "cost_reduction": {
        "current_monthly": 248.00,
        "optimized_monthly": 183.00,
        "savings": 65.00,
        "savings_percentage": 26.0
    },
    "optimization_types": ["change_instance_type"],
    "confidence_score": 0.90
}

# Aggregate statistics across all scenarios
AGGREGATE_SAVINGS = {
    "total_workloads": 6,
    "total_current_monthly_cost": 6307.00,
    "total_optimized_monthly_cost": 3490.00,
    "total_monthly_savings": 2817.00,
    "total_yearly_savings": 33804.00,
    "overall_savings_percentage": 44.7,
    "avg_confidence_score": 0.86
}

# Optimization strategy distribution
OPTIMIZATION_DISTRIBUTION = {
    "right_size_cpu": 2,
    "right_size_memory": 2,
    "reduce_replicas": 1,
    "spot_instances": 1,
    "remove_unused": 1,
    "scheduled_scaling": 1,
    "change_instance_type": 1
}

# High-confidence recommendations (>0.85)
HIGH_CONFIDENCE_RECOMMENDATIONS = [
    OVERPROVISIONED_WEB_SERVICE,
    EXCESSIVE_REPLICAS,
    SPOT_INSTANCE_CANDIDATE,
    WRONG_INSTANCE_TYPE
]

# Quick wins (high savings, low risk, high confidence)
QUICK_WINS = [
    OVERPROVISIONED_WEB_SERVICE,
    EXCESSIVE_REPLICAS,
    WRONG_INSTANCE_TYPE
]

# Multi-cloud comparison scenario
MULTI_CLOUD_COMPARISON = {
    "workload": "data-processing-job",
    "config": {
        "cpu_request": "4000m",
        "memory_request": "8Gi",
        "replicas": 5
    },
    "costs": {
        "aws": {
            "instance_type": "m5.xlarge",
            "monthly_cost": 700.80
        },
        "gcp": {
            "instance_type": "n2-standard-4",
            "monthly_cost": 657.00
        },
        "azure": {
            "instance_type": "Standard_D4s_v3",
            "monthly_cost": 700.00
        }
    },
    "recommendation": {
        "migrate_to": "gcp",
        "savings": 43.80,
        "savings_percentage": 6.25
    }
}

def get_all_scenarios():
    """Return all optimization scenarios"""
    return [
        OVERPROVISIONED_WEB_SERVICE,
        EXCESSIVE_REPLICAS,
        SPOT_INSTANCE_CANDIDATE,
        UNUSED_DEV_ENV,
        SCHEDULED_SCALING_OPPORTUNITY,
        WRONG_INSTANCE_TYPE
    ]


def get_total_savings():
    """Calculate total potential savings across all scenarios"""
    scenarios = get_all_scenarios()
    total_current = sum(s["cost_reduction"]["current_monthly"] for s in scenarios)
    total_optimized = sum(s["cost_reduction"]["optimized_monthly"] for s in scenarios)
    total_savings = total_current - total_optimized

    return {
        "total_current_monthly": total_current,
        "total_optimized_monthly": total_optimized,
        "total_monthly_savings": total_savings,
        "total_yearly_savings": total_savings * 12,
        "savings_percentage": (total_savings / total_current * 100) if total_current > 0 else 0
    }


def get_by_optimization_type(opt_type: str):
    """Get scenarios filtered by optimization type"""
    scenarios = get_all_scenarios()
    return [
        s for s in scenarios
        if opt_type in s.get("optimization_types", [])
    ]


if __name__ == "__main__":
    print("Sample Optimization Scenarios")
    print("=" * 50)

    savings = get_total_savings()
    print(f"\nTotal Current Monthly Cost: ${savings['total_current_monthly']:.2f}")
    print(f"Total Optimized Monthly Cost: ${savings['total_optimized_monthly']:.2f}")
    print(f"Total Monthly Savings: ${savings['total_monthly_savings']:.2f}")
    print(f"Total Yearly Savings: ${savings['total_yearly_savings']:.2f}")
    print(f"Overall Savings: {savings['savings_percentage']:.1f}%")

    print("\n\nTop Savings Opportunities:")
    for scenario in get_all_scenarios():
        savings_amt = scenario["cost_reduction"]["savings"]
        savings_pct = scenario["cost_reduction"]["savings_percentage"]
        print(f"  - {scenario['name']}: ${savings_amt:.2f}/mo ({savings_pct:.1f}%)")
