"""
Locust load testing for K8s Cost Optimizer API.

Simulates realistic user behavior with various workload patterns.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Target: 1000 concurrent users
"""

from locust import HttpUser, task, between, events
import random
import json
from datetime import datetime, timedelta


class OptimizerAPIUser(HttpUser):
    """Simulates a user interacting with the Optimizer API."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Called when a user starts."""
        self.cluster_id = f"cluster-{random.randint(1, 100)}"
        self.analysis_ids = []
        self.recommendation_ids = []

    @task(10)
    def view_dashboard(self):
        """View dashboard (most common action)."""
        self.client.get("/api/v1/dashboard/summary", name="/dashboard/summary")

    @task(8)
    def list_recommendations(self):
        """List available recommendations."""
        params = {
            'cluster_id': self.cluster_id,
            'status': 'pending',
            'limit': 20
        }
        with self.client.get(
            "/api/v1/recommendations",
            params=params,
            catch_response=True,
            name="/recommendations [list]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('recommendations'):
                    self.recommendation_ids = [r['id'] for r in data['recommendations'][:5]]
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)
    def get_recommendation_details(self):
        """Get details of a specific recommendation."""
        if self.recommendation_ids:
            rec_id = random.choice(self.recommendation_ids)
            self.client.get(
                f"/api/v1/recommendations/{rec_id}",
                name="/recommendations/{id}"
            )

    @task(3)
    def start_analysis(self):
        """Start a new analysis."""
        payload = {
            'cluster_id': self.cluster_id,
            'namespaces': random.sample(['production', 'staging', 'dev'], k=random.randint(1, 2)),
            'lookback_days': random.choice([7, 14, 30])
        }

        with self.client.post(
            "/api/v1/analysis",
            json=payload,
            catch_response=True,
            name="/analysis [start]"
        ) as response:
            if response.status_code in [200, 202]:
                data = response.json()
                if 'analysis_id' in data:
                    self.analysis_ids.append(data['analysis_id'])
                response.success()
            else:
                response.failure(f"Failed to start analysis: {response.status_code}")

    @task(4)
    def check_analysis_status(self):
        """Check status of running analysis."""
        if self.analysis_ids:
            analysis_id = random.choice(self.analysis_ids)
            self.client.get(
                f"/api/v1/analysis/{analysis_id}/status",
                name="/analysis/{id}/status"
            )

    @task(2)
    def get_cluster_costs(self):
        """Get current cluster costs."""
        self.client.get(
            f"/api/v1/costs/current",
            params={'cluster_id': self.cluster_id},
            name="/costs/current"
        )

    @task(2)
    def get_cost_history(self):
        """Get historical cost data."""
        self.client.get(
            f"/api/v1/costs/history",
            params={
                'cluster_id': self.cluster_id,
                'days': random.choice([7, 30, 90])
            },
            name="/costs/history"
        )

    @task(1)
    def get_cost_forecast(self):
        """Get cost forecast."""
        self.client.get(
            f"/api/v1/costs/forecast",
            params={
                'cluster_id': self.cluster_id,
                'days': 30
            },
            name="/costs/forecast"
        )

    @task(1)
    def apply_recommendation_dry_run(self):
        """Apply recommendation in dry-run mode."""
        if self.recommendation_ids:
            rec_id = random.choice(self.recommendation_ids)
            self.client.post(
                f"/api/v1/recommendations/{rec_id}/apply",
                json={'dry_run': True},
                name="/recommendations/{id}/apply [dry-run]"
            )

    @task(1)
    def list_clusters(self):
        """List all clusters."""
        self.client.get("/api/v1/clusters", name="/clusters [list]")

    @task(1)
    def get_cluster_details(self):
        """Get cluster details."""
        self.client.get(
            f"/api/v1/clusters/{self.cluster_id}",
            name="/clusters/{id}"
        )

    @task(2)
    def search_workloads(self):
        """Search for workloads."""
        self.client.get(
            "/api/v1/workloads",
            params={
                'cluster_id': self.cluster_id,
                'namespace': random.choice(['production', 'staging', 'dev'])
            },
            name="/workloads [search]"
        )


class PricingAPIUser(HttpUser):
    """Simulates users querying pricing APIs."""

    wait_time = between(2, 6)

    instance_types = {
        'aws': ['t3.micro', 't3.small', 't3.medium', 't3.large', 'm5.large', 'm5.xlarge'],
        'gcp': ['n1-standard-1', 'n1-standard-2', 'n1-standard-4', 'n2-standard-2'],
        'azure': ['Standard_B1s', 'Standard_B2s', 'Standard_D2s_v3', 'Standard_D4s_v3']
    }

    regions = {
        'aws': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'gcp': ['us-central1', 'europe-west1', 'asia-east1'],
        'azure': ['eastus', 'westus2', 'northeurope']
    }

    @task(10)
    def get_instance_price(self):
        """Get instance pricing."""
        cloud = random.choice(['aws', 'gcp', 'azure'])
        instance_type = random.choice(self.instance_types[cloud])
        region = random.choice(self.regions[cloud])

        self.client.get(
            "/api/v1/pricing/instance",
            params={
                'cloud': cloud,
                'instance_type': instance_type,
                'region': region
            },
            name="/pricing/instance"
        )

    @task(5)
    def compare_instance_prices(self):
        """Compare instance prices across clouds."""
        self.client.post(
            "/api/v1/pricing/compare",
            json={
                'cpu': random.choice([2, 4, 8]),
                'memory': random.choice([4, 8, 16, 32]),
                'region_type': 'us-east'
            },
            name="/pricing/compare"
        )

    @task(3)
    def get_storage_price(self):
        """Get storage pricing."""
        cloud = random.choice(['aws', 'gcp', 'azure'])

        self.client.get(
            "/api/v1/pricing/storage",
            params={
                'cloud': cloud,
                'storage_type': random.choice(['ssd', 'hdd']),
                'size_gb': random.choice([100, 500, 1000])
            },
            name="/pricing/storage"
        )


class AdminUser(HttpUser):
    """Simulates admin users performing management tasks."""

    wait_time = between(5, 15)

    @task(5)
    def view_all_analyses(self):
        """View all analyses across clusters."""
        self.client.get(
            "/api/v1/admin/analyses",
            params={'status': 'running'},
            name="/admin/analyses"
        )

    @task(3)
    def view_system_metrics(self):
        """View system-wide metrics."""
        self.client.get("/api/v1/admin/metrics", name="/admin/metrics")

    @task(2)
    def view_applied_recommendations(self):
        """View all applied recommendations."""
        self.client.get(
            "/api/v1/admin/recommendations/applied",
            params={'days': 30},
            name="/admin/recommendations/applied"
        )

    @task(1)
    def export_savings_report(self):
        """Export savings report."""
        self.client.post(
            "/api/v1/admin/reports/savings",
            json={
                'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'end_date': datetime.now().isoformat(),
                'format': 'json'
            },
            name="/admin/reports/savings"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print(f"\n{'='*60}")
    print(f"Starting load test: {environment.host}")
    print(f"Target: {environment.runner.target_user_count} users")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    stats = environment.stats
    print(f"\n{'='*60}")
    print(f"Load test completed!")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Median response time: {stats.total.median_response_time}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    print(f"{'='*60}\n")


# Performance thresholds for CI/CD
@events.quitting.add_listener
def check_thresholds(environment, **kwargs):
    """Check if performance thresholds are met."""
    stats = environment.stats.total

    thresholds = {
        'max_median_response_time': 500,  # 500ms
        'max_95th_percentile': 2000,  # 2 seconds
        'max_failure_rate': 0.01  # 1%
    }

    failures = []

    if stats.median_response_time > thresholds['max_median_response_time']:
        failures.append(
            f"Median response time {stats.median_response_time}ms exceeds "
            f"{thresholds['max_median_response_time']}ms"
        )

    p95 = stats.get_response_time_percentile(0.95)
    if p95 > thresholds['max_95th_percentile']:
        failures.append(
            f"95th percentile {p95}ms exceeds {thresholds['max_95th_percentile']}ms"
        )

    if stats.num_requests > 0:
        failure_rate = stats.num_failures / stats.num_requests
        if failure_rate > thresholds['max_failure_rate']:
            failures.append(
                f"Failure rate {failure_rate*100:.2f}% exceeds "
                f"{thresholds['max_failure_rate']*100:.2f}%"
            )

    if failures:
        print("\n❌ Performance thresholds NOT met:")
        for failure in failures:
            print(f"  - {failure}")
        environment.process_exit_code = 1
    else:
        print("\n✅ All performance thresholds met!")
