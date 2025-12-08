"""
Spike load test scenario.

Tests system behavior under sudden traffic spikes.
Simulates events like:
- End of month cost reviews
- Major deployment reviews
- Quarterly optimization drives
"""

from locust import HttpUser, task, between, LoadTestShape
import math


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern:
    - Start: 10 users
    - Spike to: 1000 users in 1 minute
    - Hold: 5 minutes
    - Drop to: 50 users
    - Repeat
    """

    time_limit = 1200  # 20 minutes total

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        # Calculate cycle position (10 minute cycles)
        cycle_time = run_time % 600  # 10 minute cycles

        if cycle_time < 60:  # First minute: ramp up
            user_count = int(10 + (990 * (cycle_time / 60)))
            spawn_rate = 20
        elif cycle_time < 360:  # Next 5 minutes: hold spike
            user_count = 1000
            spawn_rate = 20
        elif cycle_time < 420:  # Next minute: ramp down
            user_count = int(1000 - (950 * ((cycle_time - 360) / 60)))
            spawn_rate = 20
        else:  # Rest: low load
            user_count = 50
            spawn_rate = 5

        return (user_count, spawn_rate)


class SpikeTestUser(HttpUser):
    """User for spike testing."""
    wait_time = between(0.5, 2)

    @task
    def quick_dashboard_check(self):
        """Quick dashboard check (most common during spikes)."""
        self.client.get("/api/v1/dashboard/summary")

    @task
    def get_recommendations(self):
        """Get recommendations."""
        self.client.get("/api/v1/recommendations?limit=10")
