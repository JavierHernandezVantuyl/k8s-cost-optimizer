import logging
import httpx
from kubernetes import client
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class OptimizationHandler:

    def __init__(self, api_client, optimizer_api_url: str):
        self.api_client = api_client
        self.optimizer_api_url = optimizer_api_url
        self.apps_v1 = client.AppsV1Api(api_client)
        self.core_v1 = client.CoreV1Api(api_client)
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def analyze_workload(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str,
        optimization_type: str,
        min_confidence: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        try:
            workload = await self._get_workload(workload_name, workload_kind, namespace)
            if not workload:
                logger.warning(f"Workload {workload_kind}/{workload_name} not found in {namespace}")
                return None

            workload_id = await self._get_workload_id(workload_name, namespace)
            if not workload_id:
                logger.warning(f"Could not find workload ID for {workload_name}")
                return None

            url = f"{self.optimizer_api_url}/optimize/{workload_id}"
            logger.info(f"Fetching recommendations from {url}")

            response = await self.http_client.post(
                url,
                json={
                    "min_confidence": min_confidence,
                    "optimization_types": self._get_optimization_types(optimization_type)
                }
            )

            if response.status_code != 200:
                logger.error(f"Optimizer API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            recommendations = data.get('recommendations', [])

            if not recommendations:
                return None

            best_recommendation = max(
                recommendations,
                key=lambda r: r.get('monthly_savings', 0)
            )

            return best_recommendation

        except Exception as e:
            logger.error(f"Error analyzing workload: {str(e)}", exc_info=True)
            return None

    async def apply_optimization(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str,
        recommendation: Dict[str, Any],
        dry_run: bool = False
    ) -> bool:
        try:
            workload = await self._get_workload(workload_name, workload_kind, namespace)
            if not workload:
                logger.error(f"Workload {workload_kind}/{workload_name} not found")
                return False

            from handlers.rollback_handler import RollbackHandler
            rollback_handler = RollbackHandler(self.api_client)

            if not dry_run:
                await rollback_handler.store_original_state(
                    workload_name=workload_name,
                    workload_kind=workload_kind,
                    namespace=namespace,
                    workload=workload
                )

            recommended_config = recommendation.get('recommended_config', {})
            optimization_type = recommendation.get('optimization_type', '')

            if dry_run:
                logger.info(f"DRY-RUN: Would apply the following changes to {workload_kind}/{workload_name}:")
                logger.info(f"  Optimization Type: {optimization_type}")
                logger.info(f"  Changes: {recommended_config}")
                logger.info(f"  Savings: ${recommendation.get('monthly_savings', 0):.2f}/month")
                return True

            logger.info(f"Applying optimization to {workload_kind}/{workload_name}")

            if workload_kind == 'Deployment':
                success = await self._apply_deployment_optimization(
                    workload_name, namespace, recommended_config
                )
            elif workload_kind == 'StatefulSet':
                success = await self._apply_statefulset_optimization(
                    workload_name, namespace, recommended_config
                )
            else:
                logger.warning(f"Unsupported workload kind: {workload_kind}")
                return False

            if success:
                logger.info(f"Successfully applied optimization to {workload_kind}/{workload_name}")
            else:
                logger.error(f"Failed to apply optimization to {workload_kind}/{workload_name}")

            return success

        except Exception as e:
            logger.error(f"Error applying optimization: {str(e)}", exc_info=True)
            return False

    async def _apply_deployment_optimization(
        self,
        name: str,
        namespace: str,
        config: Dict[str, Any]
    ) -> bool:
        try:
            deployment = self.apps_v1.read_namespaced_deployment(name, namespace)

            if 'replicas' in config:
                deployment.spec.replicas = int(config['replicas'])

            if 'cpu_request' in config or 'memory_request' in config:
                for container in deployment.spec.template.spec.containers:
                    if container.resources is None:
                        container.resources = client.V1ResourceRequirements()

                    if container.resources.requests is None:
                        container.resources.requests = {}

                    if 'cpu_request' in config:
                        container.resources.requests['cpu'] = config['cpu_request']

                    if 'memory_request' in config:
                        container.resources.requests['memory'] = config['memory_request']

                    if container.resources.limits is None:
                        container.resources.limits = {}

                    if 'cpu_limit' in config:
                        container.resources.limits['cpu'] = config['cpu_limit']

                    if 'memory_limit' in config:
                        container.resources.limits['memory'] = config['memory_limit']

            if deployment.metadata.annotations is None:
                deployment.metadata.annotations = {}

            deployment.metadata.annotations['optimization.k8s.io/optimized-at'] = datetime.utcnow().isoformat()
            deployment.metadata.annotations['optimization.k8s.io/optimized-by'] = 'cost-optimizer-operator'

            self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )

            logger.info(f"Deployment {namespace}/{name} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating deployment: {str(e)}", exc_info=True)
            return False

    async def _apply_statefulset_optimization(
        self,
        name: str,
        namespace: str,
        config: Dict[str, Any]
    ) -> bool:
        try:
            statefulset = self.apps_v1.read_namespaced_stateful_set(name, namespace)

            if 'replicas' in config:
                statefulset.spec.replicas = int(config['replicas'])

            if 'cpu_request' in config or 'memory_request' in config:
                for container in statefulset.spec.template.spec.containers:
                    if container.resources is None:
                        container.resources = client.V1ResourceRequirements()

                    if container.resources.requests is None:
                        container.resources.requests = {}

                    if 'cpu_request' in config:
                        container.resources.requests['cpu'] = config['cpu_request']

                    if 'memory_request' in config:
                        container.resources.requests['memory'] = config['memory_request']

                    if container.resources.limits is None:
                        container.resources.limits = {}

                    if 'cpu_limit' in config:
                        container.resources.limits['cpu'] = config['cpu_limit']

                    if 'memory_limit' in config:
                        container.resources.limits['memory'] = config['memory_limit']

            if statefulset.metadata.annotations is None:
                statefulset.metadata.annotations = {}

            statefulset.metadata.annotations['optimization.k8s.io/optimized-at'] = datetime.utcnow().isoformat()
            statefulset.metadata.annotations['optimization.k8s.io/optimized-by'] = 'cost-optimizer-operator'

            self.apps_v1.patch_namespaced_stateful_set(
                name=name,
                namespace=namespace,
                body=statefulset
            )

            logger.info(f"StatefulSet {namespace}/{name} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating statefulset: {str(e)}", exc_info=True)
            return False

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
                logger.warning(f"Workload {kind}/{name} not found in namespace {namespace}")
                return None
            raise

    async def _get_workload_id(self, name: str, namespace: str) -> Optional[str]:
        try:
            url = f"{self.optimizer_api_url}/workloads"
            response = await self.http_client.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to fetch workloads: {response.status_code}")
                return None

            workloads = response.json().get('workloads', [])

            for workload in workloads:
                if workload.get('name') == name and workload.get('namespace') == namespace:
                    return workload.get('id')

            logger.warning(f"Workload {namespace}/{name} not found in optimizer API")
            return f"mock-{namespace}-{name}"

        except Exception as e:
            logger.error(f"Error fetching workload ID: {str(e)}")
            return f"mock-{namespace}-{name}"

    def _get_optimization_types(self, optimization_type: str) -> list:
        if optimization_type == 'ALL':
            return [
                'right_size_cpu',
                'right_size_memory',
                'reduce_replicas',
                'spot_instances',
                'scheduled_scaling'
            ]
        elif optimization_type == 'CPU':
            return ['right_size_cpu']
        elif optimization_type == 'MEMORY':
            return ['right_size_memory']
        elif optimization_type == 'REPLICAS':
            return ['reduce_replicas', 'increase_replicas']
        elif optimization_type == 'SPOT_INSTANCES':
            return ['spot_instances']
        elif optimization_type == 'SCHEDULED_SCALING':
            return ['scheduled_scaling']
        else:
            return ['right_size_cpu', 'right_size_memory']
