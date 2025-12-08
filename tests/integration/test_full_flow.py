"""
Integration tests for end-to-end optimization flow.

Tests the complete flow:
1. Collect metrics from Kubernetes
2. Analyze workloads
3. Generate recommendations
4. Apply optimizations
5. Track results
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import json


@pytest.fixture
def test_cluster_config():
    """Test cluster configuration."""
    return {
        'kubeconfig': 'tests/fixtures/test-kubeconfig.yaml',
        'context': 'test-cluster',
        'namespace': 'test-optimizer'
    }


@pytest.fixture
async def optimizer_client():
    """Create test optimizer API client."""
    from services.optimizer_api.client import OptimizerClient

    client = OptimizerClient(base_url='http://localhost:8000')
    yield client
    await client.close()


class TestEndToEndOptimizationFlow:
    """Test complete optimization workflow."""

    @pytest.mark.asyncio
    async def test_complete_optimization_cycle(self, optimizer_client):
        """Test full optimization cycle from analysis to recommendation."""

        # Step 1: Trigger analysis
        analysis_response = await optimizer_client.start_analysis({
            'cluster_id': 'test-cluster-1',
            'namespaces': ['production', 'staging'],
            'lookback_days': 7
        })

        assert analysis_response['status'] == 'started'
        analysis_id = analysis_response['analysis_id']

        # Step 2: Wait for analysis to complete
        await asyncio.sleep(5)  # In real test, poll for completion

        analysis_status = await optimizer_client.get_analysis_status(analysis_id)
        assert analysis_status['status'] == 'completed'
        assert 'workloads_analyzed' in analysis_status
        assert analysis_status['workloads_analyzed'] > 0

        # Step 3: Get recommendations
        recommendations = await optimizer_client.get_recommendations(analysis_id)

        assert len(recommendations) > 0
        assert all('type' in r for r in recommendations)
        assert all('confidence' in r for r in recommendations)
        assert all('savings' in r for r in recommendations)

        # Step 4: Apply a recommendation
        rec_to_apply = recommendations[0]
        apply_response = await optimizer_client.apply_recommendation(
            rec_to_apply['id'],
            dry_run=True
        )

        assert apply_response['status'] in ['success', 'pending']
        assert 'changes' in apply_response

    @pytest.mark.asyncio
    async def test_workload_discovery_and_analysis(self, test_cluster_config):
        """Test workload discovery and initial analysis."""
        from services.optimizer_api.collectors.k8s import K8sCollector
        from services.optimizer_api.analyzer.workload import WorkloadAnalyzer

        # Collect workloads
        collector = K8sCollector(test_cluster_config)
        workloads = await collector.discover_workloads()

        assert len(workloads) > 0
        assert all('name' in w for w in workloads)
        assert all('namespace' in w for w in workloads)

        # Analyze each workload
        analyzer = WorkloadAnalyzer()
        for workload in workloads:
            # Collect metrics
            metrics = await collector.get_metrics(
                workload['name'],
                workload['namespace'],
                days=7
            )

            # Analyze
            analysis = analyzer.analyze(workload, metrics)

            assert 'optimization_opportunities' in analysis
            assert 'current_cost' in analysis
            assert 'optimized_cost' in analysis

    @pytest.mark.asyncio
    async def test_multi_cloud_cost_comparison(self, optimizer_client):
        """Test comparing costs across multiple clouds."""

        # Define workload requirements
        requirements = {
            'workloads': [
                {'cpu': 4, 'memory': 16, 'storage': 100},  # Small
                {'cpu': 8, 'memory': 32, 'storage': 500},  # Medium
                {'cpu': 16, 'memory': 64, 'storage': 1000}  # Large
            ],
            'region': 'us-east',
            'availability': 'high'
        }

        # Get cost comparison
        comparison = await optimizer_client.compare_clouds(requirements)

        assert 'aws' in comparison
        assert 'gcp' in comparison
        assert 'azure' in comparison

        # Each cloud should have total cost and breakdown
        for cloud in ['aws', 'gcp', 'azure']:
            assert 'total_monthly_cost' in comparison[cloud]
            assert 'compute_cost' in comparison[cloud]
            assert 'storage_cost' in comparison[cloud]

        # Should identify cheapest option
        assert 'cheapest_cloud' in comparison
        assert 'savings_vs_most_expensive' in comparison


class TestRecommendationApplication:
    """Test applying recommendations to cluster."""

    @pytest.mark.asyncio
    async def test_apply_right_sizing_recommendation(self, test_cluster_config):
        """Test applying right-sizing recommendation."""
        from services.optimizer_api.applier.k8s import K8sApplier

        recommendation = {
            'type': 'right_sizing',
            'workload': {
                'name': 'test-deployment',
                'namespace': 'default',
                'kind': 'Deployment'
            },
            'changes': {
                'cpu_request': '500m',  # Down from 1000m
                'memory_request': '1Gi'  # Down from 2Gi
            }
        }

        applier = K8sApplier(test_cluster_config)

        # Apply in dry-run mode
        result = await applier.apply(recommendation, dry_run=True)

        assert result['status'] == 'success'
        assert 'diff' in result
        assert result['dry_run'] is True

        # Verify no actual changes were made
        workload = await applier.get_workload('test-deployment', 'default')
        assert workload['spec']['containers'][0]['resources']['requests']['cpu'] == '1000m'

    @pytest.mark.asyncio
    async def test_rollback_failed_optimization(self, test_cluster_config):
        """Test rolling back a failed optimization."""
        from services.optimizer_api.applier.k8s import K8sApplier

        applier = K8sApplier(test_cluster_config)

        # Save current state
        original_state = await applier.get_workload('test-deployment', 'default')

        # Apply an optimization that might fail
        recommendation = {
            'type': 'right_sizing',
            'workload': {
                'name': 'test-deployment',
                'namespace': 'default',
                'kind': 'Deployment'
            },
            'changes': {
                'cpu_request': '100m',  # Too aggressive
                'memory_request': '128Mi'
            }
        }

        apply_result = await applier.apply(recommendation)

        # Simulate failure detection
        health_check = await applier.check_health('test-deployment', 'default')

        if not health_check['healthy']:
            # Rollback
            rollback_result = await applier.rollback(
                'test-deployment',
                'default',
                original_state
            )

            assert rollback_result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_gradual_rollout_optimization(self, test_cluster_config):
        """Test gradual rollout of optimization to subset of replicas."""
        from services.optimizer_api.applier.k8s import K8sApplier

        applier = K8sApplier(test_cluster_config)

        recommendation = {
            'type': 'right_sizing',
            'workload': {
                'name': 'test-deployment',
                'namespace': 'default',
                'replicas': 10
            },
            'changes': {
                'cpu_request': '500m'
            },
            'rollout_strategy': {
                'type': 'canary',
                'percentage': 20  # Start with 20%
            }
        }

        # Phase 1: Apply to 20%
        result1 = await applier.apply_canary(recommendation, percentage=20)
        assert result1['updated_replicas'] == 2

        # Monitor for 5 minutes
        await asyncio.sleep(5)  # Simulated

        # Check metrics
        canary_metrics = await applier.get_canary_metrics('test-deployment', 'default')

        if canary_metrics['error_rate'] < 0.01 and canary_metrics['latency_increase'] < 0.1:
            # Phase 2: Expand to 100%
            result2 = await applier.apply_canary(recommendation, percentage=100)
            assert result2['updated_replicas'] == 10


class TestMonitoringAndTracking:
    """Test monitoring and tracking of optimizations."""

    @pytest.mark.asyncio
    async def test_track_optimization_impact(self, optimizer_client):
        """Test tracking impact of applied optimizations."""

        # Apply optimization
        rec_id = 'test-rec-123'
        await optimizer_client.apply_recommendation(rec_id)

        # Track for 24 hours (simulated with small wait)
        await asyncio.sleep(2)

        # Get tracking data
        tracking = await optimizer_client.get_optimization_tracking(rec_id)

        assert 'cost_before' in tracking
        assert 'cost_after' in tracking
        assert 'actual_savings' in tracking
        assert 'predicted_savings' in tracking

        # Verify savings are being realized
        assert tracking['actual_savings'] > 0

    @pytest.mark.asyncio
    async def test_alert_on_degraded_performance(self, optimizer_client):
        """Test alerting when optimization degrades performance."""

        # Create alert rule
        alert_rule = {
            'metric': 'p95_latency',
            'threshold': 1.2,  # 20% increase
            'duration': '5m'
        }

        await optimizer_client.create_alert_rule('test-deployment', alert_rule)

        # Simulate performance degradation
        # In real scenario, this would be detected by monitoring

        # Check for alerts
        alerts = await optimizer_client.get_alerts(
            workload='test-deployment',
            status='firing'
        )

        # Should have latency alert
        latency_alerts = [a for a in alerts if a['metric'] == 'p95_latency']
        if len(latency_alerts) > 0:
            # Trigger automatic rollback
            alert = latency_alerts[0]
            rollback_result = await optimizer_client.trigger_rollback(
                alert['optimization_id']
            )
            assert rollback_result['status'] == 'success'


class TestDataPersistence:
    """Test data persistence throughout optimization lifecycle."""

    @pytest.mark.asyncio
    async def test_save_and_retrieve_recommendations(self, optimizer_client):
        """Test saving recommendations to database and retrieving them."""

        # Generate recommendations
        analysis_id = 'test-analysis-456'
        recommendations = [
            {
                'type': 'right_sizing',
                'workload': 'api-service',
                'monthly_savings': 500,
                'confidence': 0.85
            },
            {
                'type': 'spot_instance',
                'workload': 'batch-job',
                'monthly_savings': 1000,
                'confidence': 0.9
            }
        ]

        # Save
        for rec in recommendations:
            rec['analysis_id'] = analysis_id
            await optimizer_client.save_recommendation(rec)

        # Retrieve
        retrieved = await optimizer_client.get_recommendations(
            analysis_id=analysis_id
        )

        assert len(retrieved) == 2
        assert retrieved[0]['analysis_id'] == analysis_id

    @pytest.mark.asyncio
    async def test_historical_optimization_data(self, optimizer_client):
        """Test querying historical optimization data."""

        # Get optimizations from last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        history = await optimizer_client.get_optimization_history(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )

        assert 'optimizations' in history
        assert 'total_savings' in history
        assert 'applied_count' in history

        # Verify data integrity
        for opt in history['optimizations']:
            assert 'timestamp' in opt
            assert 'type' in opt
            assert 'status' in opt


class TestErrorHandling:
    """Test error handling in optimization flow."""

    @pytest.mark.asyncio
    async def test_handle_insufficient_metrics(self, optimizer_client):
        """Test handling case with insufficient metrics data."""

        with pytest.raises(Exception) as exc_info:
            await optimizer_client.start_analysis({
                'cluster_id': 'new-cluster',
                'lookback_days': 7
            })

        assert 'insufficient metrics' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_handle_invalid_recommendation(self, optimizer_client):
        """Test handling invalid recommendation application."""

        invalid_rec = {
            'type': 'right_sizing',
            'workload': {
                'name': 'non-existent-deployment',
                'namespace': 'default'
            },
            'changes': {
                'cpu_request': 'invalid-value'
            }
        }

        with pytest.raises(Exception) as exc_info:
            await optimizer_client.apply_recommendation(
                'invalid-rec-id',
                recommendation=invalid_rec
            )

        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_handle_cluster_connection_failure(self, test_cluster_config):
        """Test handling cluster connection failures gracefully."""
        from services.optimizer_api.collectors.k8s import K8sCollector

        # Invalid config
        bad_config = {
            'kubeconfig': '/non/existent/path',
            'context': 'invalid-context'
        }

        collector = K8sCollector(bad_config)

        with pytest.raises(Exception) as exc_info:
            await collector.discover_workloads()

        assert 'connection' in str(exc_info.value).lower() or 'auth' in str(exc_info.value).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
