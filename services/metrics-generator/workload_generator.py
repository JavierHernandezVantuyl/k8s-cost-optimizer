import random
from typing import List, Dict


class WorkloadGenerator:

    def __init__(self):
        self.workload_templates = self._create_templates()

    def _create_templates(self) -> List[Dict]:
        templates = []

        templates.extend(self._create_web_services())
        templates.extend(self._create_databases())
        templates.extend(self._create_batch_jobs())
        templates.extend(self._create_microservices())
        templates.extend(self._create_ml_workloads())
        templates.extend(self._create_cache_services())
        templates.extend(self._create_message_queues())
        templates.extend(self._create_monitoring_stack())

        return templates

    def _create_web_services(self) -> List[Dict]:
        return [
            {
                "name": "frontend-web",
                "namespace": "production",
                "kind": "Deployment",
                "replicas": 5,
                "cpu_request": "500m",
                "memory_request": "512Mi",
                "cpu_limit": "1000m",
                "memory_limit": "1Gi",
                "workload_type": "stateless",
                "resource_profile": "balanced",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "api-gateway",
                "namespace": "production",
                "kind": "Deployment",
                "replicas": 3,
                "cpu_request": "750m",
                "memory_request": "1Gi",
                "cpu_limit": "2000m",
                "memory_limit": "2Gi",
                "workload_type": "stateless",
                "resource_profile": "cpu_intensive",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "admin-panel",
                "namespace": "production",
                "kind": "Deployment",
                "replicas": 2,
                "cpu_request": "250m",
                "memory_request": "256Mi",
                "cpu_limit": "500m",
                "memory_limit": "512Mi",
                "workload_type": "stateless",
                "resource_profile": "low_usage",
                "scaling_pattern": "steady"
            },
            {
                "name": "static-assets-cdn",
                "namespace": "production",
                "kind": "Deployment",
                "replicas": 4,
                "cpu_request": "200m",
                "memory_request": "128Mi",
                "cpu_limit": "400m",
                "memory_limit": "256Mi",
                "workload_type": "stateless",
                "resource_profile": "low_usage",
                "scaling_pattern": "steady"
            },
            {
                "name": "mobile-api",
                "namespace": "production",
                "kind": "Deployment",
                "replicas": 6,
                "cpu_request": "600m",
                "memory_request": "768Mi",
                "cpu_limit": "1500m",
                "memory_limit": "1536Mi",
                "workload_type": "stateless",
                "resource_profile": "balanced",
                "scaling_pattern": "business_hours"
            },
        ]

    def _create_databases(self) -> List[Dict]:
        return [
            {
                "name": "postgres-primary",
                "namespace": "databases",
                "kind": "StatefulSet",
                "replicas": 1,
                "cpu_request": "2000m",
                "memory_request": "4Gi",
                "cpu_limit": "4000m",
                "memory_limit": "8Gi",
                "workload_type": "database",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "steady"
            },
            {
                "name": "postgres-replica",
                "namespace": "databases",
                "kind": "StatefulSet",
                "replicas": 2,
                "cpu_request": "1500m",
                "memory_request": "3Gi",
                "cpu_limit": "3000m",
                "memory_limit": "6Gi",
                "workload_type": "database",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "steady"
            },
            {
                "name": "redis-cache",
                "namespace": "databases",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "500m",
                "memory_request": "2Gi",
                "cpu_limit": "1000m",
                "memory_limit": "4Gi",
                "workload_type": "cache",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "mongodb-sharded",
                "namespace": "databases",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "1000m",
                "memory_request": "2Gi",
                "cpu_limit": "2000m",
                "memory_limit": "4Gi",
                "workload_type": "database",
                "resource_profile": "balanced",
                "scaling_pattern": "steady"
            },
            {
                "name": "elasticsearch-cluster",
                "namespace": "databases",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "1500m",
                "memory_request": "4Gi",
                "cpu_limit": "3000m",
                "memory_limit": "8Gi",
                "workload_type": "database",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "steady"
            },
        ]

    def _create_batch_jobs(self) -> List[Dict]:
        return [
            {
                "name": "nightly-reports",
                "namespace": "batch",
                "kind": "CronJob",
                "replicas": 1,
                "cpu_request": "2000m",
                "memory_request": "4Gi",
                "cpu_limit": "4000m",
                "memory_limit": "8Gi",
                "workload_type": "batch",
                "resource_profile": "cpu_intensive",
                "scaling_pattern": "nightly"
            },
            {
                "name": "data-export",
                "namespace": "batch",
                "kind": "CronJob",
                "replicas": 1,
                "cpu_request": "1000m",
                "memory_request": "2Gi",
                "cpu_limit": "2000m",
                "memory_limit": "4Gi",
                "workload_type": "batch",
                "resource_profile": "balanced",
                "scaling_pattern": "hourly"
            },
            {
                "name": "log-aggregation",
                "namespace": "batch",
                "kind": "Job",
                "replicas": 2,
                "cpu_request": "500m",
                "memory_request": "1Gi",
                "cpu_limit": "1000m",
                "memory_limit": "2Gi",
                "workload_type": "batch",
                "resource_profile": "balanced",
                "scaling_pattern": "steady"
            },
            {
                "name": "backup-service",
                "namespace": "batch",
                "kind": "CronJob",
                "replicas": 1,
                "cpu_request": "1500m",
                "memory_request": "3Gi",
                "cpu_limit": "3000m",
                "memory_limit": "6Gi",
                "workload_type": "batch",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "nightly"
            },
        ]

    def _create_microservices(self) -> List[Dict]:
        services = []
        microservice_names = [
            "user-service", "auth-service", "payment-service", "notification-service",
            "inventory-service", "order-service", "shipping-service", "analytics-service",
            "recommendation-service", "search-service", "review-service", "catalog-service",
            "cart-service", "wishlist-service", "loyalty-service"
        ]

        for i, name in enumerate(microservice_names):
            replicas = random.randint(2, 5)
            cpu_base = random.choice([250, 500, 750, 1000])
            memory_base = random.choice([256, 512, 1024, 2048])

            services.append({
                "name": name,
                "namespace": "microservices",
                "kind": "Deployment",
                "replicas": replicas,
                "cpu_request": f"{cpu_base}m",
                "memory_request": f"{memory_base}Mi",
                "cpu_limit": f"{cpu_base * 2}m",
                "memory_limit": f"{memory_base * 2}Mi",
                "workload_type": "stateless",
                "resource_profile": "balanced",
                "scaling_pattern": random.choice(["business_hours", "steady", "weekend_low"])
            })

        return services

    def _create_ml_workloads(self) -> List[Dict]:
        return [
            {
                "name": "model-training",
                "namespace": "ml",
                "kind": "Job",
                "replicas": 1,
                "cpu_request": "8000m",
                "memory_request": "16Gi",
                "cpu_limit": "16000m",
                "memory_limit": "32Gi",
                "workload_type": "ml_training",
                "resource_profile": "cpu_intensive",
                "scaling_pattern": "sporadic"
            },
            {
                "name": "inference-api",
                "namespace": "ml",
                "kind": "Deployment",
                "replicas": 4,
                "cpu_request": "2000m",
                "memory_request": "4Gi",
                "cpu_limit": "4000m",
                "memory_limit": "8Gi",
                "workload_type": "ml_inference",
                "resource_profile": "cpu_intensive",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "feature-engineering",
                "namespace": "ml",
                "kind": "Job",
                "replicas": 2,
                "cpu_request": "4000m",
                "memory_request": "8Gi",
                "cpu_limit": "8000m",
                "memory_limit": "16Gi",
                "workload_type": "ml_training",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "nightly"
            },
        ]

    def _create_cache_services(self) -> List[Dict]:
        return [
            {
                "name": "memcached-sessions",
                "namespace": "caching",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "250m",
                "memory_request": "1Gi",
                "cpu_limit": "500m",
                "memory_limit": "2Gi",
                "workload_type": "cache",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "varnish-http",
                "namespace": "caching",
                "kind": "Deployment",
                "replicas": 4,
                "cpu_request": "500m",
                "memory_request": "512Mi",
                "cpu_limit": "1000m",
                "memory_limit": "1Gi",
                "workload_type": "cache",
                "resource_profile": "balanced",
                "scaling_pattern": "business_hours"
            },
        ]

    def _create_message_queues(self) -> List[Dict]:
        return [
            {
                "name": "rabbitmq-cluster",
                "namespace": "messaging",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "1000m",
                "memory_request": "2Gi",
                "cpu_limit": "2000m",
                "memory_limit": "4Gi",
                "workload_type": "message_queue",
                "resource_profile": "balanced",
                "scaling_pattern": "business_hours"
            },
            {
                "name": "kafka-brokers",
                "namespace": "messaging",
                "kind": "StatefulSet",
                "replicas": 3,
                "cpu_request": "1500m",
                "memory_request": "3Gi",
                "cpu_limit": "3000m",
                "memory_limit": "6Gi",
                "workload_type": "message_queue",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "steady"
            },
            {
                "name": "event-processor",
                "namespace": "messaging",
                "kind": "Deployment",
                "replicas": 5,
                "cpu_request": "750m",
                "memory_request": "1Gi",
                "cpu_limit": "1500m",
                "memory_limit": "2Gi",
                "workload_type": "stateless",
                "resource_profile": "cpu_intensive",
                "scaling_pattern": "business_hours"
            },
        ]

    def _create_monitoring_stack(self) -> List[Dict]:
        return [
            {
                "name": "prometheus-server",
                "namespace": "monitoring",
                "kind": "StatefulSet",
                "replicas": 2,
                "cpu_request": "1000m",
                "memory_request": "4Gi",
                "cpu_limit": "2000m",
                "memory_limit": "8Gi",
                "workload_type": "monitoring",
                "resource_profile": "memory_intensive",
                "scaling_pattern": "steady"
            },
            {
                "name": "grafana",
                "namespace": "monitoring",
                "kind": "Deployment",
                "replicas": 2,
                "cpu_request": "500m",
                "memory_request": "1Gi",
                "cpu_limit": "1000m",
                "memory_limit": "2Gi",
                "workload_type": "monitoring",
                "resource_profile": "balanced",
                "scaling_pattern": "steady"
            },
            {
                "name": "alertmanager",
                "namespace": "monitoring",
                "kind": "Deployment",
                "replicas": 2,
                "cpu_request": "200m",
                "memory_request": "256Mi",
                "cpu_limit": "400m",
                "memory_limit": "512Mi",
                "workload_type": "monitoring",
                "resource_profile": "low_usage",
                "scaling_pattern": "steady"
            },
            {
                "name": "node-exporter",
                "namespace": "monitoring",
                "kind": "DaemonSet",
                "replicas": 1,
                "cpu_request": "100m",
                "memory_request": "128Mi",
                "cpu_limit": "200m",
                "memory_limit": "256Mi",
                "workload_type": "monitoring",
                "resource_profile": "low_usage",
                "scaling_pattern": "steady"
            },
        ]

    def get_all_workloads(self) -> List[Dict]:
        return self.workload_templates

    def get_workloads_by_cluster(self, cluster_name: str) -> List[Dict]:
        all_workloads = self.get_all_workloads()

        if cluster_name == "aws-cluster":
            return all_workloads[0:25]
        elif cluster_name == "gcp-cluster":
            return all_workloads[25:40]
        elif cluster_name == "azure-cluster":
            return all_workloads[40:]
        else:
            return []

    def get_workload_count(self) -> int:
        return len(self.workload_templates)
