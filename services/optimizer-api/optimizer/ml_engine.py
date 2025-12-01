import numpy as np
from typing import Dict, List, Tuple
from models import Workload, WorkloadMetrics, MetricStats, ResourceSpec
import math


class MLEngine:

    def __init__(self):
        self.safety_margin = 1.15

    def right_size_resources(
        self,
        workload: Workload,
        metrics: WorkloadMetrics
    ) -> Tuple[ResourceSpec, float]:
        cpu_p95 = metrics.cpu_usage.p95
        memory_p95 = metrics.memory_usage.p95

        recommended_cpu = cpu_p95 * self.safety_margin
        recommended_memory = memory_p95 * self.safety_margin

        recommended_cpu_str = self._format_cpu(recommended_cpu)
        recommended_memory_str = self._format_memory(int(recommended_memory))

        limit_cpu = recommended_cpu * 1.5
        limit_memory = recommended_memory * 1.3

        new_spec = ResourceSpec(
            cpu_request=recommended_cpu_str,
            memory_request=recommended_memory_str,
            cpu_limit=self._format_cpu(limit_cpu),
            memory_limit=self._format_memory(int(limit_memory))
        )

        confidence = self.calculate_confidence(metrics, "right_sizing")

        return new_spec, confidence

    def detect_patterns(self, metrics: WorkloadMetrics) -> Dict:
        patterns = {
            "has_business_hours_pattern": False,
            "has_weekend_pattern": False,
            "has_burst_pattern": False,
            "has_steady_pattern": False,
            "recommended_scaling": "none"
        }

        cpu_variance = self._calculate_variance(metrics.cpu_usage)
        memory_variance = self._calculate_variance(metrics.memory_usage)

        if cpu_variance > 0.4 or memory_variance > 0.3:
            patterns["has_burst_pattern"] = True
            patterns["recommended_scaling"] = "horizontal"
        elif cpu_variance < 0.15 and memory_variance < 0.15:
            patterns["has_steady_pattern"] = True
            patterns["recommended_scaling"] = "none"
        else:
            patterns["has_business_hours_pattern"] = True
            patterns["recommended_scaling"] = "scheduled"

        if metrics.cpu_utilization_pct < 30 and metrics.memory_utilization_pct < 30:
            patterns["recommended_scaling"] = "downsize"

        return patterns

    def optimize_replicas(
        self,
        workload: Workload,
        metrics: WorkloadMetrics,
        target_utilization: float = 70.0
    ) -> Tuple[int, float]:
        current_replicas = workload.replicas
        avg_cpu_util = metrics.cpu_utilization_pct
        avg_memory_util = metrics.memory_utilization_pct

        max_utilization = max(avg_cpu_util, avg_memory_util)

        if max_utilization < 30:
            recommended_replicas = max(1, current_replicas - 1)
            if max_utilization < 15:
                recommended_replicas = max(1, math.ceil(current_replicas * 0.5))
        elif max_utilization > 85:
            recommended_replicas = math.ceil(current_replicas * (max_utilization / target_utilization))
        else:
            optimal_replicas = current_replicas * (max_utilization / target_utilization)
            recommended_replicas = max(1, round(optimal_replicas))

        if workload.kind == "StatefulSet" and recommended_replicas < current_replicas:
            recommended_replicas = current_replicas

        confidence = self.calculate_confidence(metrics, "replica_optimization")

        if abs(recommended_replicas - current_replicas) / current_replicas < 0.15:
            recommended_replicas = current_replicas

        return recommended_replicas, confidence

    def calculate_confidence(self, metrics: WorkloadMetrics, optimization_type: str) -> float:
        base_confidence = 0.5

        if metrics.sample_count > 1000:
            base_confidence += 0.2
        elif metrics.sample_count > 500:
            base_confidence += 0.15
        elif metrics.sample_count > 100:
            base_confidence += 0.1

        cpu_variance = self._calculate_variance(metrics.cpu_usage)
        memory_variance = self._calculate_variance(metrics.memory_usage)
        avg_variance = (cpu_variance + memory_variance) / 2

        if avg_variance < 0.15:
            base_confidence += 0.2
        elif avg_variance < 0.3:
            base_confidence += 0.1

        if metrics.time_range_hours >= 168:
            base_confidence += 0.1
        elif metrics.time_range_hours >= 72:
            base_confidence += 0.05

        if optimization_type == "right_sizing":
            if metrics.cpu_utilization_pct < 20 or metrics.cpu_utilization_pct > 90:
                base_confidence += 0.05

        return min(1.0, base_confidence)

    def bin_packing(self, workloads: List[Dict], node_capacity: Dict) -> Dict:
        sorted_workloads = sorted(
            workloads,
            key=lambda w: (w.get("cpu_request", 0) + w.get("memory_request", 0)),
            reverse=True
        )

        nodes = []
        current_node = {
            "cpu_used": 0,
            "memory_used": 0,
            "cpu_capacity": node_capacity.get("cpu", 8.0),
            "memory_capacity": node_capacity.get("memory", 32 * 1024 * 1024 * 1024),
            "workloads": []
        }

        for workload in sorted_workloads:
            cpu_needed = workload.get("cpu_request", 0)
            memory_needed = workload.get("memory_request", 0)

            if (current_node["cpu_used"] + cpu_needed <= current_node["cpu_capacity"] * 0.85 and
                current_node["memory_used"] + memory_needed <= current_node["memory_capacity"] * 0.85):
                current_node["cpu_used"] += cpu_needed
                current_node["memory_used"] += memory_needed
                current_node["workloads"].append(workload)
            else:
                nodes.append(current_node)
                current_node = {
                    "cpu_used": cpu_needed,
                    "memory_used": memory_needed,
                    "cpu_capacity": node_capacity.get("cpu", 8.0),
                    "memory_capacity": node_capacity.get("memory", 32 * 1024 * 1024 * 1024),
                    "workloads": [workload]
                }

        if current_node["workloads"]:
            nodes.append(current_node)

        total_cpu_utilization = sum(n["cpu_used"] for n in nodes) / sum(n["cpu_capacity"] for n in nodes) if nodes else 0
        total_memory_utilization = sum(n["memory_used"] for n in nodes) / sum(n["memory_capacity"] for n in nodes) if nodes else 0

        return {
            "required_nodes": len(nodes),
            "total_cpu_utilization": total_cpu_utilization * 100,
            "total_memory_utilization": total_memory_utilization * 100,
            "nodes": nodes,
            "savings_potential": max(0, len(workloads) - len(nodes))
        }

    def detect_unused_resources(self, metrics: WorkloadMetrics, threshold_pct: float = 5.0) -> bool:
        if metrics.cpu_utilization_pct < threshold_pct and metrics.memory_utilization_pct < threshold_pct:
            return True
        return False

    def recommend_spot_instances(self, workload: Workload, metrics: WorkloadMetrics) -> Tuple[bool, float, str]:
        is_suitable = True
        confidence = 0.7
        reason = ""

        if workload.kind in ["StatefulSet", "DaemonSet"]:
            is_suitable = False
            reason = "StatefulSets and DaemonSets are not suitable for spot instances"
            return is_suitable, 0.0, reason

        patterns = self.detect_patterns(metrics)
        if patterns["has_burst_pattern"]:
            confidence -= 0.2
            reason = "Burst pattern detected, spot interruptions may impact performance"

        if metrics.cpu_utilization_pct > 80 or metrics.memory_utilization_pct > 80:
            confidence -= 0.15
            reason = "High utilization may be impacted by spot interruptions"

        if workload.replicas == 1:
            is_suitable = False
            confidence = 0.0
            reason = "Single replica workload, spot interruptions would cause downtime"
            return is_suitable, confidence, reason

        if is_suitable and not reason:
            reason = "Workload is suitable for spot instances with appropriate redundancy"

        return is_suitable, confidence, reason

    def recommend_instance_type_change(
        self,
        current_cpu: float,
        current_memory: float,
        provider: str
    ) -> Tuple[str, str]:
        if provider.lower() == "aws":
            if current_cpu / current_memory > 0.5:
                return "c5.xlarge", "CPU-optimized instance recommended"
            elif current_memory / current_cpu > 4:
                return "r5.large", "Memory-optimized instance recommended"
            else:
                return "m5.large", "Balanced instance recommended"

        elif provider.lower() == "gcp":
            if current_cpu / current_memory > 0.5:
                return "c2-standard-4", "Compute-optimized instance recommended"
            elif current_memory / current_cpu > 4:
                return "n2-highmem-2", "Memory-optimized instance recommended"
            else:
                return "n2-standard-2", "Balanced instance recommended"

        else:
            if current_cpu / current_memory > 0.5:
                return "Standard_F4s_v2", "Compute-optimized instance recommended"
            elif current_memory / current_cpu > 4:
                return "Standard_E4s_v3", "Memory-optimized instance recommended"
            else:
                return "Standard_D4s_v3", "Balanced instance recommended"

    def detect_scheduled_scaling_opportunity(self, metrics: WorkloadMetrics) -> Dict:
        patterns = self.detect_patterns(metrics)

        if patterns["has_business_hours_pattern"]:
            return {
                "suitable": True,
                "strategy": "business_hours",
                "peak_hours": "9am-5pm weekdays",
                "off_peak_scale_down": 0.5,
                "confidence": 0.75
            }
        elif patterns["has_weekend_pattern"]:
            return {
                "suitable": True,
                "strategy": "weekend_reduction",
                "peak_days": "Monday-Friday",
                "weekend_scale_down": 0.3,
                "confidence": 0.7
            }
        else:
            return {
                "suitable": False,
                "strategy": "none",
                "confidence": 0.0
            }

    def _calculate_variance(self, stats: MetricStats) -> float:
        if stats.avg == 0:
            return 0.0

        variance = (stats.p95 - stats.p50) / stats.avg if stats.avg > 0 else 0
        return abs(variance)

    def _format_cpu(self, cpu_cores: float) -> str:
        if cpu_cores < 1:
            return f"{int(cpu_cores * 1000)}m"
        return f"{cpu_cores:.1f}"

    def _format_memory(self, memory_bytes: int) -> str:
        if memory_bytes < 1024 * 1024:
            return f"{memory_bytes // 1024}Ki"
        elif memory_bytes < 1024 * 1024 * 1024:
            return f"{memory_bytes // (1024 * 1024)}Mi"
        else:
            return f"{memory_bytes // (1024 * 1024 * 1024)}Gi"

    def _parse_cpu(self, cpu_string: str) -> float:
        if cpu_string.endswith('m'):
            return float(cpu_string[:-1]) / 1000
        return float(cpu_string)

    def _parse_memory(self, memory_string: str) -> int:
        multipliers = {
            'Ki': 1024,
            'Mi': 1024 * 1024,
            'Gi': 1024 * 1024 * 1024
        }
        for suffix, multiplier in multipliers.items():
            if memory_string.endswith(suffix):
                return int(float(memory_string[:-len(suffix)]) * multiplier)
        return int(memory_string)
