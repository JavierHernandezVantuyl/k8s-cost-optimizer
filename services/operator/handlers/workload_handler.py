import logging
import httpx
from kubernetes import client
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WorkloadHandler:

    def __init__(self, api_client, optimizer_api_url: str):
        self.api_client = api_client
        self.optimizer_api_url = optimizer_api_url
        self.apps_v1 = client.AppsV1Api(api_client)
        self.core_v1 = client.CoreV1Api(api_client)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def watch_deployments(self, namespace: str = None) -> List[Dict[str, Any]]:
        try:
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()

            workloads = []
            for deployment in deployments.items:
                workload_info = self._extract_workload_info(deployment, 'Deployment')
                workloads.append(workload_info)

            logger.info(f"Found {len(workloads)} deployments")
            return workloads

        except Exception as e:
            logger.error(f"Error watching deployments: {str(e)}", exc_info=True)
            return []

    async def watch_statefulsets(self, namespace: str = None) -> List[Dict[str, Any]]:
        try:
            if namespace:
                statefulsets = self.apps_v1.list_namespaced_stateful_set(namespace)
            else:
                statefulsets = self.apps_v1.list_stateful_set_for_all_namespaces()

            workloads = []
            for statefulset in statefulsets.items:
                workload_info = self._extract_workload_info(statefulset, 'StatefulSet')
                workloads.append(workload_info)

            logger.info(f"Found {len(workloads)} statefulsets")
            return workloads

        except Exception as e:
            logger.error(f"Error watching statefulsets: {str(e)}", exc_info=True)
            return []

    async def calculate_usage(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.optimizer_api_url}/workloads/{namespace}/{workload_name}/metrics"
            response = await self.http_client.get(url)

            if response.status_code != 200:
                logger.warning(
                    f"Could not fetch metrics for {workload_kind}/{workload_name}: "
                    f"{response.status_code}"
                )
                return None

            metrics = response.json()
            return metrics

        except Exception as e:
            logger.error(f"Error calculating usage: {str(e)}", exc_info=True)
            return None

    async def validate_optimization(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str,
        recommended_config: Dict[str, Any],
        max_change_percent: int = 50
    ) -> tuple[bool, str]:
        try:
            workload = await self._get_workload(workload_name, workload_kind, namespace)
            if not workload:
                return False, f"Workload {workload_kind}/{workload_name} not found"

            current_replicas = workload.spec.replicas or 1

            if 'replicas' in recommended_config:
                new_replicas = int(recommended_config['replicas'])
                change_percent = abs(new_replicas - current_replicas) / current_replicas * 100

                if change_percent > max_change_percent:
                    return False, (
                        f"Replica change of {change_percent:.1f}% exceeds "
                        f"maximum allowed {max_change_percent}%"
                    )

                if new_replicas < 1:
                    return False, "Cannot reduce replicas below 1"

                if workload_kind == 'StatefulSet' and new_replicas < current_replicas:
                    return False, "Reducing StatefulSet replicas requires manual intervention"

            current_resources = self._get_current_resources(workload)

            if 'cpu_request' in recommended_config:
                current_cpu = self._parse_cpu(current_resources.get('cpu_request', '0'))
                new_cpu = self._parse_cpu(recommended_config['cpu_request'])
                change_percent = abs(new_cpu - current_cpu) / current_cpu * 100 if current_cpu > 0 else 0

                if change_percent > max_change_percent:
                    return False, (
                        f"CPU change of {change_percent:.1f}% exceeds "
                        f"maximum allowed {max_change_percent}%"
                    )

            if 'memory_request' in recommended_config:
                current_mem = self._parse_memory(current_resources.get('memory_request', '0'))
                new_mem = self._parse_memory(recommended_config['memory_request'])
                change_percent = abs(new_mem - current_mem) / current_mem * 100 if current_mem > 0 else 0

                if change_percent > max_change_percent:
                    return False, (
                        f"Memory change of {change_percent:.1f}% exceeds "
                        f"maximum allowed {max_change_percent}%"
                    )

            pod_disruption_budget = await self._check_pod_disruption_budget(namespace, workload_name)
            if pod_disruption_budget and 'replicas' in recommended_config:
                new_replicas = int(recommended_config['replicas'])
                min_available = pod_disruption_budget.get('minAvailable', 1)

                if new_replicas < min_available:
                    return False, (
                        f"New replica count {new_replicas} would violate "
                        f"PodDisruptionBudget minAvailable={min_available}"
                    )

            return True, "Validation passed"

        except Exception as e:
            logger.error(f"Error validating optimization: {str(e)}", exc_info=True)
            return False, f"Validation error: {str(e)}"

    def _extract_workload_info(self, workload, kind: str) -> Dict[str, Any]:
        containers = workload.spec.template.spec.containers
        resources = self._get_current_resources_from_spec(containers)

        return {
            'name': workload.metadata.name,
            'namespace': workload.metadata.namespace,
            'kind': kind,
            'replicas': workload.spec.replicas,
            'resources': resources,
            'labels': workload.metadata.labels or {},
            'annotations': workload.metadata.annotations or {},
            'creation_timestamp': workload.metadata.creation_timestamp.isoformat()
        }

    def _get_current_resources_from_spec(self, containers) -> Dict[str, str]:
        if not containers:
            return {}

        container = containers[0]
        resources = {}

        if container.resources:
            if container.resources.requests:
                resources['cpu_request'] = container.resources.requests.get('cpu', '0')
                resources['memory_request'] = container.resources.requests.get('memory', '0')

            if container.resources.limits:
                resources['cpu_limit'] = container.resources.limits.get('cpu', '0')
                resources['memory_limit'] = container.resources.limits.get('memory', '0')

        return resources

    def _get_current_resources(self, workload) -> Dict[str, str]:
        containers = workload.spec.template.spec.containers
        return self._get_current_resources_from_spec(containers)

    async def _get_workload(
        self,
        name: str,
        kind: str,
        namespace: str
    ) -> Optional[Any]:
        try:
            if kind == 'Deployment':
                return self.apps_v1.read_namespaced_deployment(name, namespace)
            elif kind == 'StatefulSet':
                return self.apps_v1.read_namespaced_stateful_set(name, namespace)
            elif kind == 'DaemonSet':
                return self.apps_v1.read_namespaced_daemon_set(name, namespace)
            else:
                logger.warning(f"Unsupported workload kind: {kind}")
                return None
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return None
            raise

    async def _check_pod_disruption_budget(
        self,
        namespace: str,
        workload_name: str
    ) -> Optional[Dict[str, Any]]:
        try:
            policy_v1 = client.PolicyV1Api(self.api_client)
            pdbs = policy_v1.list_namespaced_pod_disruption_budget(namespace)

            for pdb in pdbs.items:
                selector = pdb.spec.selector
                if selector and selector.match_labels:
                    return {
                        'name': pdb.metadata.name,
                        'minAvailable': pdb.spec.min_available,
                        'maxUnavailable': pdb.spec.max_unavailable
                    }

            return None

        except Exception as e:
            logger.debug(f"Error checking PDB: {str(e)}")
            return None

    def _parse_cpu(self, cpu_str: str) -> float:
        if not cpu_str or cpu_str == '0':
            return 0.0

        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        else:
            return float(cpu_str)

    def _parse_memory(self, mem_str: str) -> float:
        if not mem_str or mem_str == '0':
            return 0.0

        units = {
            'Ki': 1024,
            'Mi': 1024 ** 2,
            'Gi': 1024 ** 3,
            'Ti': 1024 ** 4,
            'K': 1000,
            'M': 1000 ** 2,
            'G': 1000 ** 3,
            'T': 1000 ** 4
        }

        for unit, multiplier in units.items():
            if mem_str.endswith(unit):
                return float(mem_str[:-len(unit)]) * multiplier

        return float(mem_str)
