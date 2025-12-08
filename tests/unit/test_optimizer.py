"""
Unit tests for optimization algorithms.

Tests cover:
- Resource optimization algorithms
- Bin packing strategies
- Right-sizing calculations
- Spot instance recommendations
- Scaling recommendations
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import numpy as np


@pytest.fixture
def sample_workload():
    """Sample workload data."""
    return {
        'name': 'web-app',
        'namespace': 'production',
        'type': 'Deployment',
        'replicas': 3,
        'containers': [{
            'name': 'nginx',
            'requests': {
                'cpu': '500m',
                'memory': '512Mi'
            },
            'limits': {
                'cpu': '1000m',
                'memory': '1Gi'
            },
            'actual_usage': {
                'cpu_avg': '200m',
                'cpu_p95': '350m',
                'memory_avg': '256Mi',
                'memory_p95': '400Mi'
            }
        }]
    }


@pytest.fixture
def sample_metrics():
    """Sample metrics data over 7 days."""
    days = 7
    samples_per_day = 24  # Hourly
    total_samples = days * samples_per_day

    timestamps = [
        datetime.now() - timedelta(hours=i)
        for i in range(total_samples)
    ]

    return {
        'timestamps': timestamps,
        'cpu': np.random.normal(200, 50, total_samples),  # Mean 200m, stddev 50m
        'memory': np.random.normal(256, 30, total_samples),  # Mean 256Mi, stddev 30Mi
        'requests': np.random.poisson(100, total_samples)  # Requests per minute
    }


class TestResourceOptimizer:
    """Test resource optimization algorithms."""

    def test_right_sizing_over_provisioned(self, sample_workload):
        """Test right-sizing for over-provisioned workload."""
        from services.optimizer_api.optimizer.resource import ResourceOptimizer

        optimizer = ResourceOptimizer()
        recommendations = optimizer.optimize(sample_workload)

        # Current: 500m CPU requested, 200m average usage
        # Should recommend reduction
        assert recommendations['cpu']['recommended'] < 500
        assert recommendations['cpu']['recommended'] >= 200  # Should still cover average
        assert recommendations['cpu']['savings_percent'] > 0

    def test_right_sizing_under_provisioned(self):
        """Test right-sizing for under-provisioned workload."""
        from services.optimizer_api.optimizer.resource import ResourceOptimizer

        workload = {
            'name': 'api-service',
            'containers': [{
                'requests': {'cpu': '100m', 'memory': '256Mi'},
                'limits': {'cpu': '200m', 'memory': '512Mi'},
                'actual_usage': {
                    'cpu_avg': '180m',  # Near limit
                    'cpu_p95': '195m',
                    'memory_avg': '480Mi',
                    'memory_p95': '500Mi'
                }
            }]
        }

        optimizer = ResourceOptimizer()
        recommendations = optimizer.optimize(workload)

        # Should recommend increase
        assert recommendations['cpu']['recommended'] > 100
        assert recommendations['memory']['recommended'] > 256
        assert recommendations['risk_level'] == 'high'

    def test_right_sizing_with_headroom(self, sample_workload):
        """Test that recommendations include safety headroom."""
        from services.optimizer_api.optimizer.resource import ResourceOptimizer

        optimizer = ResourceOptimizer(headroom_percent=20)
        recommendations = optimizer.optimize(sample_workload)

        # P95 usage is 350m, with 20% headroom should recommend ~420m
        expected_min = 350 * 1.20
        assert recommendations['cpu']['recommended'] >= expected_min

    def test_optimization_with_spiky_workload(self):
        """Test optimization for workloads with high variability."""
        from services.optimizer_api.optimizer.resource import ResourceOptimizer

        workload = {
            'name': 'batch-processor',
            'containers': [{
                'requests': {'cpu': '1000m'},
                'actual_usage': {
                    'cpu_avg': '200m',
                    'cpu_p95': '900m',  # High spike
                    'cpu_max': '1500m'
                }
            }]
        }

        optimizer = ResourceOptimizer()
        recommendations = optimizer.optimize(workload)

        # Should use P95 or P99 instead of average due to high variability
        assert recommendations['cpu']['recommended'] > 200
        assert recommendations['cpu']['strategy'] == 'p95_based'


class TestBinPacking:
    """Test bin packing algorithms for node optimization."""

    def test_first_fit_decreasing(self):
        """Test first-fit decreasing bin packing."""
        from services.optimizer_api.optimizer.binpack import BinPacker

        # List of pod resource requirements
        pods = [
            {'cpu': 1000, 'memory': 2048},  # 1 CPU, 2GB
            {'cpu': 500, 'memory': 1024},
            {'cpu': 2000, 'memory': 4096},
            {'cpu': 1500, 'memory': 2048},
            {'cpu': 250, 'memory': 512},
        ]

        # Node capacity
        node_capacity = {'cpu': 4000, 'memory': 8192}  # 4 CPU, 8GB

        packer = BinPacker(algorithm='first_fit_decreasing')
        result = packer.pack(pods, node_capacity)

        assert result['num_nodes'] >= 2  # Can't fit all in one node
        assert result['utilization'] > 0.5  # Should achieve decent utilization
        assert len(result['unscheduled']) == 0  # All pods should fit

    def test_best_fit_packing(self):
        """Test best-fit bin packing for better utilization."""
        from services.optimizer_api.optimizer.binpack import BinPacker

        pods = [
            {'cpu': 1000, 'memory': 1024},
            {'cpu': 2000, 'memory': 2048},
            {'cpu': 500, 'memory': 512},
            {'cpu': 1500, 'memory': 1024},
        ]

        node_capacity = {'cpu': 4000, 'memory': 4096}

        packer = BinPacker(algorithm='best_fit')
        result = packer.pack(pods, node_capacity)

        # Best fit should achieve better utilization than first fit
        assert result['avg_utilization'] > 0.6

    def test_node_affinity_constraints(self):
        """Test bin packing with affinity constraints."""
        from services.optimizer_api.optimizer.binpack import BinPacker

        pods = [
            {'cpu': 1000, 'memory': 1024, 'affinity': 'ssd'},
            {'cpu': 1000, 'memory': 1024, 'affinity': 'ssd'},
            {'cpu': 1000, 'memory': 1024, 'affinity': 'hdd'},
        ]

        nodes = [
            {'cpu': 4000, 'memory': 4096, 'type': 'ssd'},
            {'cpu': 4000, 'memory': 4096, 'type': 'hdd'},
        ]

        packer = BinPacker()
        result = packer.pack_with_constraints(pods, nodes)

        # Verify affinity is respected
        for assignment in result['assignments']:
            if assignment['pod']['affinity'] == 'ssd':
                assert assignment['node']['type'] == 'ssd'


class TestSpotInstanceOptimizer:
    """Test spot instance optimization."""

    def test_spot_instance_recommendation(self):
        """Test spot instance recommendations for suitable workloads."""
        from services.optimizer_api.optimizer.spot import SpotOptimizer

        workload = {
            'name': 'batch-job',
            'type': 'Job',
            'fault_tolerant': True,
            'priority': 'low',
            'duration': '2h'
        }

        optimizer = SpotOptimizer()
        recommendation = optimizer.analyze(workload)

        assert recommendation['spot_suitable'] is True
        assert recommendation['savings_percent'] > 50  # Spot typically 50-90% cheaper
        assert 'interruption_risk' in recommendation

    def test_spot_not_recommended_for_critical(self):
        """Test that spot is not recommended for critical workloads."""
        from services.optimizer_api.optimizer.spot import SpotOptimizer

        workload = {
            'name': 'payment-api',
            'type': 'Deployment',
            'fault_tolerant': False,
            'priority': 'critical',
            'sla': '99.99%'
        }

        optimizer = SpotOptimizer()
        recommendation = optimizer.analyze(workload)

        assert recommendation['spot_suitable'] is False
        assert 'reasons' in recommendation

    def test_mixed_spot_on_demand_strategy(self):
        """Test hybrid spot/on-demand recommendation."""
        from services.optimizer_api.optimizer.spot import SpotOptimizer

        workload = {
            'name': 'web-service',
            'replicas': 10,
            'fault_tolerant': True,
            'min_replicas': 3
        }

        optimizer = SpotOptimizer()
        recommendation = optimizer.analyze(workload)

        # Should recommend keeping minimum on on-demand
        assert recommendation['strategy'] == 'mixed'
        assert recommendation['on_demand_count'] >= 3
        assert recommendation['spot_count'] > 0
        assert recommendation['on_demand_count'] + recommendation['spot_count'] == 10


class TestHorizontalScalingOptimizer:
    """Test horizontal scaling optimization."""

    def test_scale_up_recommendation(self, sample_metrics):
        """Test scale-up recommendation based on high utilization."""
        from services.optimizer_api.optimizer.scaling import ScalingOptimizer

        workload = {
            'name': 'api',
            'current_replicas': 3,
            'min_replicas': 2,
            'max_replicas': 20,
            'target_cpu': 70  # Target 70% CPU
        }

        # Simulate 85% average CPU usage
        metrics = sample_metrics.copy()
        metrics['cpu'] = np.ones(len(metrics['cpu'])) * 850  # 850m = 85% of 1 CPU

        optimizer = ScalingOptimizer()
        recommendation = optimizer.analyze(workload, metrics)

        assert recommendation['action'] == 'scale_up'
        assert recommendation['recommended_replicas'] > 3
        assert recommendation['reason'] == 'high_cpu_utilization'

    def test_scale_down_recommendation(self, sample_metrics):
        """Test scale-down recommendation based on low utilization."""
        from services.optimizer_api.optimizer.scaling import ScalingOptimizer

        workload = {
            'name': 'worker',
            'current_replicas': 10,
            'min_replicas': 2,
            'max_replicas': 20,
            'target_cpu': 70
        }

        # Simulate 20% average CPU usage
        metrics = sample_metrics.copy()
        metrics['cpu'] = np.ones(len(metrics['cpu'])) * 200  # 200m = 20% of 1 CPU

        optimizer = ScalingOptimizer()
        recommendation = optimizer.analyze(workload, metrics)

        assert recommendation['action'] == 'scale_down'
        assert recommendation['recommended_replicas'] < 10
        assert recommendation['recommended_replicas'] >= 2  # Respect min

    def test_predictive_scaling(self):
        """Test predictive scaling based on historical patterns."""
        from services.optimizer_api.optimizer.scaling import ScalingOptimizer

        # Create traffic pattern with daily cycle
        hours = 168  # 7 days
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(hours)]

        # Simulate daily pattern: high during business hours, low at night
        traffic = []
        for ts in timestamps:
            hour = ts.hour
            if 9 <= hour <= 17:  # Business hours
                traffic.append(np.random.normal(1000, 100))
            else:
                traffic.append(np.random.normal(200, 50))

        metrics = {
            'timestamps': timestamps,
            'requests': traffic
        }

        optimizer = ScalingOptimizer(enable_prediction=True)
        schedule = optimizer.predict_scaling_schedule(metrics)

        # Should have different replica counts for different times
        assert len(schedule) > 1
        assert schedule['business_hours']['replicas'] > schedule['night']['replicas']


class TestVerticalScalingOptimizer:
    """Test vertical scaling (VPA) optimization."""

    def test_vpa_recommendation(self, sample_workload):
        """Test VPA recommendations for CPU and memory."""
        from services.optimizer_api.optimizer.vpa import VPAOptimizer

        optimizer = VPAOptimizer()
        recommendation = optimizer.analyze(sample_workload)

        assert 'cpu' in recommendation
        assert 'memory' in recommendation

        # Should have target, lower bound, and upper bound
        assert 'target' in recommendation['cpu']
        assert 'lowerBound' in recommendation['cpu']
        assert 'upperBound' in recommendation['cpu']

    def test_vpa_with_oom_history(self):
        """Test VPA recommendations when OOM kills occurred."""
        from services.optimizer_api.optimizer.vpa import VPAOptimizer

        workload = {
            'name': 'memory-intensive',
            'containers': [{
                'requests': {'memory': '512Mi'},
                'actual_usage': {'memory_avg': '480Mi'},
                'oom_kills': 5  # Had 5 OOM kills
            }]
        }

        optimizer = VPAOptimizer()
        recommendation = optimizer.analyze(workload)

        # Should significantly increase memory
        assert recommendation['memory']['target'] > 512
        assert recommendation['priority'] == 'high'
        assert 'oom_risk' in recommendation['warnings']


class TestCostOptimizer:
    """Test overall cost optimization."""

    def test_multi_strategy_optimization(self):
        """Test combining multiple optimization strategies."""
        from services.optimizer_api.optimizer.cost import CostOptimizer

        cluster_state = {
            'workloads': [
                {
                    'name': 'over-provisioned-app',
                    'requests': {'cpu': '2000m'},
                    'usage': {'cpu_avg': '500m'}
                },
                {
                    'name': 'spot-candidate',
                    'type': 'Job',
                    'fault_tolerant': True
                }
            ],
            'nodes': [
                {'type': 'm5.xlarge', 'utilization': 30},
                {'type': 'm5.2xlarge', 'utilization': 25}
            ]
        }

        optimizer = CostOptimizer()
        recommendations = optimizer.optimize(cluster_state)

        # Should have multiple types of recommendations
        assert 'right_sizing' in recommendations
        assert 'spot_instances' in recommendations
        assert 'node_consolidation' in recommendations
        assert 'total_savings' in recommendations

    def test_savings_calculation(self):
        """Test accurate savings calculation."""
        from services.optimizer_api.optimizer.cost import CostOptimizer

        current_costs = {
            'compute': 5000,  # $5000/month
            'storage': 1000,
            'network': 500
        }

        optimizations = [
            {'type': 'right_sizing', 'savings': 1500},
            {'type': 'spot_instances', 'savings': 1000},
            {'type': 'storage_optimization', 'savings': 300}
        ]

        optimizer = CostOptimizer()
        result = optimizer.calculate_savings(current_costs, optimizations)

        assert result['current_cost'] == 6500
        assert result['optimized_cost'] == 3700
        assert result['total_savings'] == 2800
        assert result['savings_percent'] == pytest.approx(43.08, 0.01)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
