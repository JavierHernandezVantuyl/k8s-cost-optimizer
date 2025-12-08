"""
Stress test scenario.

Gradually increases load to find breaking point.
Tests system stability under increasing load.
"""

from locust import HttpUser, task, between, LoadTestShape


class StressTestShape(LoadTestShape):
    """
    Gradually increase load until failure:
    - Start: 100 users
    - Increase: 100 users every 2 minutes
    - Max: 2000 users
    - Duration: 40 minutes
    """

    stages = [
        {"duration": 120, "users": 100, "spawn_rate": 10},
        {"duration": 240, "users": 200, "spawn_rate": 10},
        {"duration": 360, "users": 300, "spawn_rate": 10},
        {"duration": 480, "users": 400, "spawn_rate": 10},
        {"duration": 600, "users": 500, "spawn_rate": 10},
        {"duration": 720, "users": 750, "spawn_rate": 15},
        {"duration": 840, "users": 1000, "spawn_rate": 15},
        {"duration": 960, "users": 1250, "spawn_rate": 15},
        {"duration": 1080, "users": 1500, "spawn_rate": 20},
        {"duration": 1200, "users": 1750, "spawn_rate": 20},
        {"duration": 1320, "users": 2000, "spawn_rate": 20},
        {"duration": 1440, "users": 2000, "spawn_rate": 20},  # Hold at 2000
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None


class StressTestUser(HttpUser):
    """User for stress testing with realistic behavior."""
    wait_time = between(1, 3)

    @task(5)
    def api_calls(self):
        """Mixed API calls."""
        endpoints = [
            "/api/v1/dashboard/summary",
            "/api/v1/recommendations",
            "/api/v1/costs/current",
            "/api/v1/clusters"
        ]
        import random
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)

    @task(1)
    def intensive_operation(self):
        """Intensive operation like starting analysis."""
        self.client.post("/api/v1/analysis", json={
            "cluster_id": f"cluster-{self.environment.runner.user_count}",
            "namespaces": ["production"],
            "lookback_days": 7
        })
