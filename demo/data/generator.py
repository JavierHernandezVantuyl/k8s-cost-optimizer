"""
Demo Data Generator for K8s Cost Optimizer.

Generates realistic workload data showing impressive cost savings:
- 100+ diverse workloads
- 30 days of historical metrics
- 35-45% potential cost reduction
- Multiple optimization opportunities
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np


class WorkloadGenerator:
    """Generate realistic Kubernetes workload configurations."""

    WORKLOAD_TYPES = ['Deployment', 'StatefulSet', 'DaemonSet', 'CronJob', 'Job']
    NAMESPACES = ['production', 'staging', 'dev', 'ml', 'analytics', 'monitoring']

    APP_TEMPLATES = [
        # Over-provisioned web applications
        {
            'name_prefix': 'web-app',
            'type': 'Deployment',
            'replicas': (3, 10),
            'cpu_request': '1000m',
            'memory_request': '2Gi',
            'cpu_usage_avg': '250m',  # 25% utilization
            'memory_usage_avg': '800Mi',  # 40% utilization
            'savings_potential': 0.45  # 45% savings
        },
        # Over-provisioned APIs
        {
            'name_prefix': 'api-service',
            'type': 'Deployment',
            'replicas': (5, 15),
            'cpu_request': '2000m',
            'memory_request': '4Gi',
            'cpu_usage_avg': '600m',  # 30% utilization
            'memory_usage_avg': '1.5Gi',  # 37.5% utilization
            'savings_potential': 0.42
        },
        # Batch jobs (good spot candidates)
        {
            'name_prefix': 'batch-processor',
            'type': 'CronJob',
            'replicas': (1, 5),
            'cpu_request': '4000m',
            'memory_request': '8Gi',
            'cpu_usage_avg': '3500m',  # Well utilized
            'memory_usage_avg': '6Gi',
            'savings_potential': 0.65,  # 65% with spot instances
            'spot_suitable': True
        },
        # Databases (slightly over-provisioned)
        {
            'name_prefix': 'database',
            'type': 'StatefulSet',
            'replicas': (1, 3),
            'cpu_request': '8000m',
            'memory_request': '16Gi',
            'cpu_usage_avg': '5000m',
            'memory_usage_avg': '12Gi',
            'savings_potential': 0.25,  # Conservative for databases
            'spot_suitable': False
        },
        # Worker queues
        {
            'name_prefix': 'worker',
            'type': 'Deployment',
            'replicas': (10, 50),
            'cpu_request': '500m',
            'memory_request': '1Gi',
            'cpu_usage_avg': '150m',  # Bursty workload
            'memory_usage_avg': '400Mi',
            'savings_potential': 0.50,  # High savings with HPA
            'hpa_suitable': True
        },
        # ML training jobs
        {
            'name_prefix': 'ml-training',
            'type': 'Job',
            'replicas': (1, 1),
            'cpu_request': '16000m',
            'memory_request': '32Gi',
            'cpu_usage_avg': '14000m',
            'memory_usage_avg': '28Gi',
            'savings_potential': 0.70,  # Spot instances for non-critical training
            'spot_suitable': True
        },
        # Monitoring/logging
        {
            'name_prefix': 'monitoring',
            'type': 'DaemonSet',
            'replicas': (1, 1),  # One per node
            'cpu_request': '200m',
            'memory_request': '512Mi',
            'cpu_usage_avg': '100m',
            'memory_usage_avg': '300Mi',
            'savings_potential': 0.35
        }
    ]

    def generate_workloads(self, count: int = 100) -> List[Dict]:
        """Generate specified number of workloads."""
        workloads = []

        for i in range(count):
            template = random.choice(self.APP_TEMPLATES)

            workload = {
                'name': f"{template['name_prefix']}-{i:03d}",
                'namespace': random.choice(self.NAMESPACES),
                'type': template['type'],
                'replicas': random.randint(*template['replicas']) if isinstance(template['replicas'], tuple) else template['replicas'],
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                'labels': {
                    'app': template['name_prefix'],
                    'team': random.choice(['backend', 'frontend', 'data', 'ml', 'platform']),
                    'environment': random.choice(['production', 'staging', 'dev'])
                },
                'resources': {
                    'requests': {
                        'cpu': template['cpu_request'],
                        'memory': template['memory_request']
                    },
                    'limits': {
                        'cpu': self._multiply_resource(template['cpu_request'], 2),
                        'memory': self._multiply_resource(template['memory_request'], 2)
                    }
                },
                'usage': {
                    'cpu_avg': template['cpu_usage_avg'],
                    'cpu_p95': self._add_variance(template['cpu_usage_avg'], 0.15),
                    'cpu_p99': self._add_variance(template['cpu_usage_avg'], 0.25),
                    'memory_avg': template['memory_usage_avg'],
                    'memory_p95': self._add_variance(template['memory_usage_avg'], 0.10),
                    'memory_p99': self._add_variance(template['memory_usage_avg'], 0.15),
                },
                'optimization': {
                    'savings_potential_percent': template['savings_potential'] * 100,
                    'spot_suitable': template.get('spot_suitable', False),
                    'hpa_suitable': template.get('hpa_suitable', False)
                }
            }

            workloads.append(workload)

        return workloads

    def _multiply_resource(self, resource: str, multiplier: float) -> str:
        """Multiply resource value."""
        if resource.endswith('m'):
            value = int(resource[:-1])
            return f"{int(value * multiplier)}m"
        elif resource.endswith('Gi'):
            value = float(resource[:-2])
            return f"{value * multiplier}Gi"
        elif resource.endswith('Mi'):
            value = float(resource[:-2])
            return f"{value * multiplier}Mi"
        return resource

    def _add_variance(self, resource: str, variance: float) -> str:
        """Add variance to resource value."""
        if resource.endswith('m'):
            value = int(resource[:-1])
            new_value = int(value * (1 + variance))
            return f"{new_value}m"
        elif resource.endswith('Gi'):
            value = float(resource[:-2])
            new_value = round(value * (1 + variance), 1)
            return f"{new_value}Gi"
        elif resource.endswith('Mi'):
            value = float(resource[:-2])
            new_value = round(value * (1 + variance))
            return f"{new_value}Mi"
        return resource


class MetricsGenerator:
    """Generate 30 days of historical metrics."""

    def generate_metrics(self, workload: Dict, days: int = 30) -> List[Dict]:
        """Generate time-series metrics for a workload."""
        metrics = []
        cpu_avg = self._parse_resource(workload['usage']['cpu_avg'])
        memory_avg = self._parse_resource(workload['usage']['memory_avg'])

        # Generate hourly metrics for 30 days
        for hour in range(days * 24):
            timestamp = datetime.now() - timedelta(hours=days*24 - hour)

            # Add daily and weekly patterns
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()

            # Business hours pattern (higher usage 9-5 on weekdays)
            if 9 <= hour_of_day <= 17 and day_of_week < 5:
                load_multiplier = random.uniform(1.2, 1.5)
            else:
                load_multiplier = random.uniform(0.6, 1.0)

            # Add random spikes (5% chance)
            if random.random() < 0.05:
                load_multiplier *= random.uniform(2.0, 3.0)

            cpu_value = cpu_avg * load_multiplier + random.gauss(0, cpu_avg * 0.1)
            memory_value = memory_avg * load_multiplier + random.gauss(0, memory_avg * 0.05)

            metrics.append({
                'timestamp': timestamp.isoformat(),
                'cpu': max(0, cpu_value),
                'memory': max(0, memory_value),
                'network_in': random.uniform(1000, 10000),  # KB/s
                'network_out': random.uniform(500, 5000),
                'requests_per_sec': max(0, random.gauss(100 * load_multiplier, 30))
            })

        return metrics

    def _parse_resource(self, resource: str) -> float:
        """Parse resource string to numeric value."""
        if resource.endswith('m'):
            return int(resource[:-1])
        elif resource.endswith('Gi'):
            return float(resource[:-2]) * 1024  # Convert to Mi
        elif resource.endswith('Mi'):
            return float(resource[:-2])
        return float(resource)


class CostCalculator:
    """Calculate costs for workloads."""

    PRICING = {
        'cpu_per_core_hour': 0.031,  # $0.031 per vCPU hour
        'memory_per_gb_hour': 0.0035,  # $0.0035 per GB hour
        'spot_discount': 0.70  # 70% discount for spot
    }

    def calculate_current_cost(self, workload: Dict) -> Dict:
        """Calculate current monthly cost."""
        cpu = self._parse_cpu(workload['resources']['requests']['cpu'])
        memory = self._parse_memory(workload['resources']['requests']['memory'])
        replicas = workload['replicas']

        hours_per_month = 730  # Average

        cpu_cost = cpu * replicas * self.PRICING['cpu_per_core_hour'] * hours_per_month
        memory_cost = memory * replicas * self.PRICING['memory_per_gb_hour'] * hours_per_month

        return {
            'compute': round(cpu_cost + memory_cost, 2),
            'storage': round(random.uniform(10, 100), 2),  # Simplified
            'network': round(random.uniform(5, 50), 2),
            'total': round(cpu_cost + memory_cost + random.uniform(15, 150), 2)
        }

    def calculate_optimized_cost(self, workload: Dict, current_cost: Dict) -> Dict:
        """Calculate optimized cost based on potential savings."""
        savings_rate = workload['optimization']['savings_potential_percent'] / 100
        optimized_total = current_cost['total'] * (1 - savings_rate)

        return {
            'compute': round(current_cost['compute'] * (1 - savings_rate), 2),
            'storage': current_cost['storage'],  # No storage optimization in this demo
            'network': current_cost['network'],  # No network optimization in this demo
            'total': round(optimized_total, 2),
            'monthly_savings': round(current_cost['total'] - optimized_total, 2),
            'annual_savings': round((current_cost['total'] - optimized_total) * 12, 2)
        }

    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU to cores."""
        if cpu_str.endswith('m'):
            return int(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def _parse_memory(self, mem_str: str) -> float:
        """Parse memory to GB."""
        if mem_str.endswith('Gi'):
            return float(mem_str[:-2])
        elif mem_str.endswith('Mi'):
            return float(mem_str[:-2]) / 1024
        return float(mem_str)


def generate_demo_data(output_dir: str = 'demo/data'):
    """Generate complete demo dataset."""
    import os

    os.makedirs(output_dir, exist_ok=True)

    print("Generating demo data...")

    # Generate workloads
    print("  - Generating 120 workloads...")
    workload_gen = WorkloadGenerator()
    workloads = workload_gen.generate_workloads(120)

    # Generate metrics for each workload
    print("  - Generating 30 days of metrics...")
    metrics_gen = MetricsGenerator()
    cost_calc = CostCalculator()

    total_current_cost = 0
    total_optimized_cost = 0

    detailed_workloads = []
    for i, workload in enumerate(workloads):
        if i % 20 == 0:
            print(f"    Processing workload {i}/{len(workloads)}...")

        # Generate metrics
        metrics = metrics_gen.generate_metrics(workload)

        # Calculate costs
        current_cost = cost_calc.calculate_current_cost(workload)
        optimized_cost = cost_calc.calculate_optimized_cost(workload, current_cost)

        total_current_cost += current_cost['total']
        total_optimized_cost += optimized_cost['total']

        detailed_workload = {
            **workload,
            'metrics': metrics[-168:],  # Last 7 days (hourly)
            'cost': {
                'current': current_cost,
                'optimized': optimized_cost
            }
        }

        detailed_workloads.append(detailed_workload)

    # Save workloads
    with open(f'{output_dir}/workloads.json', 'w') as f:
        json.dump(detailed_workloads, f, indent=2)

    # Generate summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_workloads': len(detailed_workloads),
        'total_current_monthly_cost': round(total_current_cost, 2),
        'total_optimized_monthly_cost': round(total_optimized_cost, 2),
        'total_monthly_savings': round(total_current_cost - total_optimized_cost, 2),
        'total_annual_savings': round((total_current_cost - total_optimized_cost) * 12, 2),
        'savings_percentage': round(((total_current_cost - total_optimized_cost) / total_current_cost) * 100, 2),
        'by_namespace': {},
        'by_team': {}
    }

    # Calculate breakdowns
    for workload in detailed_workloads:
        ns = workload['namespace']
        team = workload['labels']['team']

        if ns not in summary['by_namespace']:
            summary['by_namespace'][ns] = {'current': 0, 'optimized': 0, 'count': 0}
        if team not in summary['by_team']:
            summary['by_team'][team] = {'current': 0, 'optimized': 0, 'count': 0}

        summary['by_namespace'][ns]['current'] += workload['cost']['current']['total']
        summary['by_namespace'][ns]['optimized'] += workload['cost']['optimized']['total']
        summary['by_namespace'][ns]['count'] += 1

        summary['by_team'][team]['current'] += workload['cost']['current']['total']
        summary['by_team'][team]['optimized'] += workload['cost']['optimized']['total']
        summary['by_team'][team]['count'] += 1

    with open(f'{output_dir}/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Demo data generated successfully!")
    print(f"   Workloads: {summary['total_workloads']}")
    print(f"   Current monthly cost: ${summary['total_current_monthly_cost']:,.2f}")
    print(f"   Optimized monthly cost: ${summary['total_optimized_monthly_cost']:,.2f}")
    print(f"   Monthly savings: ${summary['total_monthly_savings']:,.2f}")
    print(f"   Annual savings: ${summary['total_annual_savings']:,.2f}")
    print(f"   Savings percentage: {summary['savings_percentage']}%")
    print(f"\n   Data saved to: {output_dir}/")


if __name__ == '__main__':
    generate_demo_data()
