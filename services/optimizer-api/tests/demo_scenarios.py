#!/usr/bin/env python3

import sys
import json
from sample_data import (
    get_all_scenarios,
    get_total_savings,
    get_by_optimization_type,
    AGGREGATE_SAVINGS,
    HIGH_CONFIDENCE_RECOMMENDATIONS,
    QUICK_WINS,
    MULTI_CLOUD_COMPARISON
)


def print_separator(title=""):
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def print_scenario(scenario, detailed=False):
    print(f"Workload: {scenario['name']}")
    print(f"Optimization: {', '.join(scenario['optimization_types'])}")
    print(f"Confidence: {scenario['confidence_score']:.0%}")

    cost = scenario['cost_reduction']
    print(f"Current Cost: ${cost['current_monthly']:.2f}/month")
    print(f"Optimized Cost: ${cost['optimized_monthly']:.2f}/month")
    print(f"Savings: ${cost['savings']:.2f}/month ({cost['savings_percentage']:.1f}%)")

    if detailed:
        if 'current_config' in scenario:
            print(f"\nCurrent Config:")
            for key, value in scenario['current_config'].items():
                print(f"  {key}: {value}")

        if 'recommended_config' in scenario:
            print(f"\nRecommended Config:")
            for key, value in scenario['recommended_config'].items():
                print(f"  {key}: {value}")

        if 'actual_usage' in scenario:
            usage = scenario['actual_usage']
            print(f"\nActual Usage:")
            print(f"  CPU: {usage['cpu_avg']} avg, {usage['cpu_p95']} p95 ({usage['cpu_utilization_pct']:.1f}% utilization)")
            print(f"  Memory: {usage['memory_avg']} avg, {usage['memory_p95']} p95 ({usage['memory_utilization_pct']:.1f}% utilization)")

    print()


def main():
    print_separator("K8s Cost Optimizer - Optimization Scenarios Demo")

    print("This demo shows realistic optimization scenarios demonstrating 35-40% cost reduction")
    print("across different workload types and optimization strategies.")

    print_separator("AGGREGATE SAVINGS OVERVIEW")

    savings = get_total_savings()
    print(f"Total Workloads Analyzed: {AGGREGATE_SAVINGS['total_workloads']}")
    print(f"Total Current Monthly Cost: ${savings['total_current_monthly']:.2f}")
    print(f"Total Optimized Monthly Cost: ${savings['total_optimized_monthly']:.2f}")
    print(f"Total Monthly Savings: ${savings['total_monthly_savings']:.2f}")
    print(f"Total Yearly Savings: ${savings['total_yearly_savings']:.2f}")
    print(f"Overall Savings Percentage: {savings['savings_percentage']:.1f}%")

    print_separator("ALL OPTIMIZATION SCENARIOS")

    scenarios = get_all_scenarios()
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. ", end="")
        print_scenario(scenario)

    print_separator("HIGH-CONFIDENCE RECOMMENDATIONS (>85% confidence)")

    print(f"Found {len(HIGH_CONFIDENCE_RECOMMENDATIONS)} high-confidence recommendations:\n")
    for i, scenario in enumerate(HIGH_CONFIDENCE_RECOMMENDATIONS, 1):
        print(f"{i}. ", end="")
        print_scenario(scenario)

    print_separator("QUICK WINS (High savings, low risk, high confidence)")

    print(f"Found {len(QUICK_WINS)} quick win opportunities:\n")
    total_quick_win_savings = sum(s['cost_reduction']['savings'] for s in QUICK_WINS)
    print(f"Combined Monthly Savings from Quick Wins: ${total_quick_win_savings:.2f}\n")

    for i, scenario in enumerate(QUICK_WINS, 1):
        print(f"{i}. ", end="")
        print_scenario(scenario, detailed=True)

    print_separator("OPTIMIZATION BY TYPE")

    opt_types = set()
    for scenario in scenarios:
        opt_types.update(scenario['optimization_types'])

    for opt_type in sorted(opt_types):
        matching = get_by_optimization_type(opt_type)
        total_savings = sum(s['cost_reduction']['savings'] for s in matching)
        print(f"{opt_type.replace('_', ' ').title()}")
        print(f"  Workloads: {len(matching)}")
        print(f"  Total Savings: ${total_savings:.2f}/month")
        print()

    print_separator("MULTI-CLOUD COST COMPARISON")

    print(f"Workload: {MULTI_CLOUD_COMPARISON['workload']}")
    print(f"\nConfiguration:")
    for key, value in MULTI_CLOUD_COMPARISON['config'].items():
        print(f"  {key}: {value}")

    print(f"\nCloud Provider Costs:")
    costs = MULTI_CLOUD_COMPARISON['costs']
    for provider, details in costs.items():
        print(f"  {provider.upper()}: ${details['monthly_cost']:.2f}/month ({details['instance_type']})")

    rec = MULTI_CLOUD_COMPARISON['recommendation']
    print(f"\nRecommendation: Migrate to {rec['migrate_to'].upper()}")
    print(f"Savings: ${rec['savings']:.2f}/month ({rec['savings_percentage']:.1f}%)")

    print_separator("KEY INSIGHTS")

    print("1. Right-Sizing Opportunities:")
    print("   Most workloads are over-provisioned with 20-30% utilization")
    print("   Rightsizing to P95 usage + 15% safety margin saves 40-50%")
    print()

    print("2. Replica Optimization:")
    print("   Many services run with excessive replica counts")
    print("   Reducing replicas to match actual load saves 30-40%")
    print()

    print("3. Spot Instances:")
    print("   Fault-tolerant batch workloads can use spot instances")
    print("   Spot instances provide 60-70% cost reduction")
    print()

    print("4. Scheduled Scaling:")
    print("   Business-hours workloads can scale down during off-peak")
    print("   Scheduled scaling provides 35-40% savings")
    print()

    print("5. Unused Resources:")
    print("   Development environments often run 24/7 with minimal usage")
    print("   Removing or scheduling these saves 100% of their cost")

    print_separator()

    print("Export this data:")
    print("  - CSV format for reporting")
    print("  - Terraform format for infrastructure as code")
    print("  - JSON format for API integration")
    print()

    print("Next steps:")
    print("  1. Start the optimizer-api service: make start")
    print("  2. Run the test suite: ./services/optimizer-api/tests/test_api.sh")
    print("  3. View in Grafana: http://localhost:3000")
    print()


if __name__ == "__main__":
    main()
