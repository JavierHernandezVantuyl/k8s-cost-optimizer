import random
import math
from datetime import datetime, timedelta
from typing import Dict, Tuple
import numpy as np


class MetricsSimulator:

    def __init__(self):
        self.baseline_multipliers = {}
        self.growth_rate = 0.001

    def generate_cpu_usage(self, workload: Dict, timestamp: datetime = None) -> float:
        if timestamp is None:
            timestamp = datetime.utcnow()

        cpu_request_cores = self._parse_cpu(workload["cpu_request"])
        cpu_limit_cores = self._parse_cpu(workload["cpu_limit"])

        base_usage = self._get_base_usage(workload, "cpu")

        business_hours_factor = self._get_business_hours_factor(timestamp)
        weekend_factor = self._get_weekend_factor(timestamp)
        workload_pattern_factor = self._get_workload_pattern_factor(
            workload["scaling_pattern"], timestamp
        )
        spike_factor = self._get_spike_factor()
        growth_factor = self._get_growth_factor(timestamp)

        combined_factor = (
            business_hours_factor *
            weekend_factor *
            workload_pattern_factor *
            spike_factor *
            growth_factor
        )

        usage = base_usage * combined_factor

        if workload["resource_profile"] == "cpu_intensive":
            usage = min(usage * random.uniform(1.2, 1.5), cpu_limit_cores)
        elif workload["resource_profile"] == "low_usage":
            usage = usage * random.uniform(0.3, 0.6)

        usage = max(0.01, min(usage, cpu_limit_cores * 0.95))

        return round(usage, 4)

    def generate_memory_usage(self, workload: Dict, timestamp: datetime = None) -> int:
        if timestamp is None:
            timestamp = datetime.utcnow()

        memory_request_bytes = self._parse_memory(workload["memory_request"])
        memory_limit_bytes = self._parse_memory(workload["memory_limit"])

        base_usage = memory_request_bytes * random.uniform(0.6, 0.9)

        business_hours_factor = self._get_business_hours_factor(timestamp, intensity=0.3)
        weekend_factor = self._get_weekend_factor(timestamp, intensity=0.2)
        workload_pattern_factor = self._get_workload_pattern_factor(
            workload["scaling_pattern"], timestamp, intensity=0.2
        )
        growth_factor = self._get_growth_factor(timestamp, intensity=0.5)

        combined_factor = (
            business_hours_factor *
            weekend_factor *
            workload_pattern_factor *
            growth_factor
        )

        usage = base_usage * combined_factor

        if workload["resource_profile"] == "memory_intensive":
            usage = min(usage * random.uniform(1.3, 1.6), memory_limit_bytes)
        elif workload["resource_profile"] == "low_usage":
            usage = usage * random.uniform(0.4, 0.7)

        usage = max(memory_request_bytes * 0.2, min(usage, memory_limit_bytes * 0.95))

        return int(usage)

    def generate_network_traffic(self, workload: Dict, timestamp: datetime = None) -> Tuple[int, int]:
        if timestamp is None:
            timestamp = datetime.utcnow()

        base_rate = self._get_base_network_rate(workload["workload_type"])

        business_hours_factor = self._get_business_hours_factor(timestamp)
        weekend_factor = self._get_weekend_factor(timestamp)
        spike_factor = self._get_spike_factor(probability=0.05)

        combined_factor = business_hours_factor * weekend_factor * spike_factor

        rx_bytes = int(base_rate * combined_factor * random.uniform(0.8, 1.2))
        tx_bytes = int(rx_bytes * random.uniform(0.3, 0.8))

        return rx_bytes, tx_bytes

    def _parse_cpu(self, cpu_string: str) -> float:
        if cpu_string.endswith('m'):
            return float(cpu_string[:-1]) / 1000
        return float(cpu_string)

    def _parse_memory(self, memory_string: str) -> int:
        multipliers = {
            'Ki': 1024,
            'Mi': 1024 * 1024,
            'Gi': 1024 * 1024 * 1024,
            'K': 1000,
            'M': 1000 * 1000,
            'G': 1000 * 1000 * 1000
        }

        for suffix, multiplier in multipliers.items():
            if memory_string.endswith(suffix):
                return int(float(memory_string[:-len(suffix)]) * multiplier)

        return int(memory_string)

    def _get_base_usage(self, workload: Dict, resource_type: str) -> float:
        key = f"{workload['name']}_{resource_type}"

        if key not in self.baseline_multipliers:
            if resource_type == "cpu":
                cpu_request = self._parse_cpu(workload["cpu_request"])
                self.baseline_multipliers[key] = cpu_request * random.uniform(0.4, 0.8)
            else:
                self.baseline_multipliers[key] = random.uniform(0.5, 0.8)

        return self.baseline_multipliers[key]

    def _get_business_hours_factor(self, timestamp: datetime, intensity: float = 1.0) -> float:
        hour = timestamp.hour
        minute = timestamp.minute

        if 9 <= hour < 17:
            peak_position = (hour - 9) / 8
            peak_curve = math.sin(peak_position * math.pi)
            return 1.0 + (peak_curve * 0.5 * intensity)
        elif 7 <= hour < 9 or 17 <= hour < 19:
            return 1.0 + (0.2 * intensity)
        elif 19 <= hour < 22:
            return 1.0 - (0.2 * intensity)
        else:
            return 1.0 - (0.4 * intensity)

    def _get_weekend_factor(self, timestamp: datetime, intensity: float = 1.0) -> float:
        weekday = timestamp.weekday()

        if weekday >= 5:
            return 1.0 - (0.3 * intensity)
        return 1.0

    def _get_workload_pattern_factor(self, pattern: str, timestamp: datetime, intensity: float = 1.0) -> float:
        hour = timestamp.hour

        if pattern == "business_hours":
            if 9 <= hour < 17:
                return 1.0 + (0.4 * intensity)
            return 1.0 - (0.3 * intensity)

        elif pattern == "nightly":
            if 0 <= hour < 6:
                return 1.0 + (2.0 * intensity)
            return 1.0 - (0.8 * intensity)

        elif pattern == "hourly":
            minute_factor = (timestamp.minute % 60) / 60
            if minute_factor < 0.2:
                return 1.0 + (0.5 * intensity)
            return 1.0

        elif pattern == "sporadic":
            return random.uniform(0.2, 2.0) if random.random() < 0.1 else 1.0

        elif pattern == "weekend_low":
            if timestamp.weekday() >= 5:
                return 1.0 - (0.5 * intensity)
            return 1.0 + (0.2 * intensity)

        else:
            return 1.0

    def _get_spike_factor(self, probability: float = 0.02) -> float:
        if random.random() < probability:
            return random.uniform(1.5, 3.0)
        return 1.0

    def _get_growth_factor(self, timestamp: datetime, intensity: float = 1.0) -> float:
        days_elapsed = (timestamp - datetime(2024, 1, 1)).days
        growth = 1.0 + (days_elapsed * self.growth_rate * intensity)
        return min(growth, 1.5)

    def _get_base_network_rate(self, workload_type: str) -> int:
        network_rates = {
            "stateless": 5 * 1024 * 1024,
            "database": 50 * 1024 * 1024,
            "cache": 100 * 1024 * 1024,
            "batch": 20 * 1024 * 1024,
            "ml_training": 500 * 1024 * 1024,
            "ml_inference": 30 * 1024 * 1024,
            "message_queue": 80 * 1024 * 1024,
            "monitoring": 10 * 1024 * 1024
        }

        return network_rates.get(workload_type, 10 * 1024 * 1024)

    def generate_historical_metrics(
        self,
        workload: Dict,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 5
    ) -> list:
        metrics = []
        current_time = start_time

        while current_time <= end_time:
            cpu_usage = self.generate_cpu_usage(workload, current_time)
            memory_usage = self.generate_memory_usage(workload, current_time)
            rx_bytes, tx_bytes = self.generate_network_traffic(workload, current_time)

            metrics.append({
                "timestamp": current_time,
                "cpu_usage_cores": cpu_usage,
                "memory_usage_bytes": memory_usage,
                "network_rx_bytes": rx_bytes,
                "network_tx_bytes": tx_bytes
            })

            current_time += timedelta(minutes=interval_minutes)

        return metrics
