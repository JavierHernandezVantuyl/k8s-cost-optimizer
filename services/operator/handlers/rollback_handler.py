import logging
import json
import redis
from kubernetes import client
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class RollbackHandler:

    def __init__(self, api_client):
        self.api_client = api_client
        self.apps_v1 = client.AppsV1Api(api_client)
        self.core_v1 = client.CoreV1Api(api_client)

        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))

        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}. Rollback functionality limited.")
            self.redis_client = None

    async def store_original_state(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str,
        workload: Any
    ) -> bool:
        try:
            state = {
                'workload_name': workload_name,
                'workload_kind': workload_kind,
                'namespace': namespace,
                'replicas': workload.spec.replicas,
                'resources': self._extract_resources(workload),
                'timestamp': datetime.utcnow().isoformat(),
                'annotations': dict(workload.metadata.annotations or {}),
                'labels': dict(workload.metadata.labels or {})
            }

            key = f"rollback:{namespace}:{workload_kind}:{workload_name}"

            if self.redis_client:
                self.redis_client.setex(
                    key,
                    timedelta(days=7),
                    json.dumps(state)
                )
                logger.info(f"Stored original state for {workload_kind}/{workload_name} in Redis")
            else:
                logger.warning(f"Redis not available. Cannot store rollback state for {workload_kind}/{workload_name}")

            configmap_name = f"{workload_name}-rollback-state"
            await self._store_in_configmap(namespace, configmap_name, state)

            return True

        except Exception as e:
            logger.error(f"Error storing original state: {str(e)}", exc_info=True)
            return False

    async def execute_rollback(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str
    ) -> bool:
        try:
            logger.info(f"Executing rollback for {workload_kind}/{workload_name} in {namespace}")

            original_state = await self._get_original_state(
                workload_name, workload_kind, namespace
            )

            if not original_state:
                logger.error(f"No rollback state found for {workload_kind}/{workload_name}")
                return False

            logger.info(f"Found original state: {original_state}")

            if workload_kind == 'Deployment':
                success = await self._rollback_deployment(namespace, workload_name, original_state)
            elif workload_kind == 'StatefulSet':
                success = await self._rollback_statefulset(namespace, workload_name, original_state)
            else:
                logger.error(f"Unsupported workload kind for rollback: {workload_kind}")
                return False

            if success:
                logger.info(f"Successfully rolled back {workload_kind}/{workload_name}")
                await self.validate_rollback(workload_name, workload_kind, namespace, original_state)
            else:
                logger.error(f"Failed to rollback {workload_kind}/{workload_name}")

            return success

        except Exception as e:
            logger.error(f"Error executing rollback: {str(e)}", exc_info=True)
            return False

    async def validate_rollback(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str,
        original_state: Dict[str, Any]
    ) -> bool:
        try:
            workload = await self._get_workload(workload_name, workload_kind, namespace)
            if not workload:
                logger.error(f"Workload {workload_kind}/{workload_name} not found after rollback")
                return False

            current_replicas = workload.spec.replicas
            expected_replicas = original_state.get('replicas')

            if current_replicas != expected_replicas:
                logger.warning(
                    f"Replica count mismatch after rollback: "
                    f"expected {expected_replicas}, got {current_replicas}"
                )
                return False

            current_resources = self._extract_resources(workload)
            expected_resources = original_state.get('resources', {})

            for key in ['cpu_request', 'memory_request']:
                if key in expected_resources:
                    if current_resources.get(key) != expected_resources.get(key):
                        logger.warning(
                            f"Resource mismatch after rollback for {key}: "
                            f"expected {expected_resources.get(key)}, got {current_resources.get(key)}"
                        )
                        return False

            logger.info(f"Rollback validation passed for {workload_kind}/{workload_name}")
            return True

        except Exception as e:
            logger.error(f"Error validating rollback: {str(e)}", exc_info=True)
            return False

    async def _rollback_deployment(
        self,
        namespace: str,
        name: str,
        original_state: Dict[str, Any]
    ) -> bool:
        try:
            deployment = self.apps_v1.read_namespaced_deployment(name, namespace)

            deployment.spec.replicas = original_state.get('replicas', 1)

            resources = original_state.get('resources', {})
            for container in deployment.spec.template.spec.containers:
                if container.resources is None:
                    container.resources = client.V1ResourceRequirements()

                if container.resources.requests is None:
                    container.resources.requests = {}

                if 'cpu_request' in resources:
                    container.resources.requests['cpu'] = resources['cpu_request']

                if 'memory_request' in resources:
                    container.resources.requests['memory'] = resources['memory_request']

                if container.resources.limits is None:
                    container.resources.limits = {}

                if 'cpu_limit' in resources:
                    container.resources.limits['cpu'] = resources['cpu_limit']

                if 'memory_limit' in resources:
                    container.resources.limits['memory'] = resources['memory_limit']

            if deployment.metadata.annotations is None:
                deployment.metadata.annotations = {}

            deployment.metadata.annotations['optimization.k8s.io/rolled-back-at'] = datetime.utcnow().isoformat()
            deployment.metadata.annotations['optimization.k8s.io/rolled-back-by'] = 'cost-optimizer-operator'

            self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )

            logger.info(f"Rolled back deployment {namespace}/{name}")
            return True

        except Exception as e:
            logger.error(f"Error rolling back deployment: {str(e)}", exc_info=True)
            return False

    async def _rollback_statefulset(
        self,
        namespace: str,
        name: str,
        original_state: Dict[str, Any]
    ) -> bool:
        try:
            statefulset = self.apps_v1.read_namespaced_stateful_set(name, namespace)

            statefulset.spec.replicas = original_state.get('replicas', 1)

            resources = original_state.get('resources', {})
            for container in statefulset.spec.template.spec.containers:
                if container.resources is None:
                    container.resources = client.V1ResourceRequirements()

                if container.resources.requests is None:
                    container.resources.requests = {}

                if 'cpu_request' in resources:
                    container.resources.requests['cpu'] = resources['cpu_request']

                if 'memory_request' in resources:
                    container.resources.requests['memory'] = resources['memory_request']

                if container.resources.limits is None:
                    container.resources.limits = {}

                if 'cpu_limit' in resources:
                    container.resources.limits['cpu'] = resources['cpu_limit']

                if 'memory_limit' in resources:
                    container.resources.limits['memory'] = resources['memory_limit']

            if statefulset.metadata.annotations is None:
                statefulset.metadata.annotations = {}

            statefulset.metadata.annotations['optimization.k8s.io/rolled-back-at'] = datetime.utcnow().isoformat()
            statefulset.metadata.annotations['optimization.k8s.io/rolled-back-by'] = 'cost-optimizer-operator'

            self.apps_v1.patch_namespaced_stateful_set(
                name=name,
                namespace=namespace,
                body=statefulset
            )

            logger.info(f"Rolled back statefulset {namespace}/{name}")
            return True

        except Exception as e:
            logger.error(f"Error rolling back statefulset: {str(e)}", exc_info=True)
            return False

    async def _get_original_state(
        self,
        workload_name: str,
        workload_kind: str,
        namespace: str
    ) -> Optional[Dict[str, Any]]:
        key = f"rollback:{namespace}:{workload_kind}:{workload_name}"

        if self.redis_client:
            try:
                state_json = self.redis_client.get(key)
                if state_json:
                    logger.info(f"Retrieved rollback state from Redis for {workload_kind}/{workload_name}")
                    return json.loads(state_json)
            except Exception as e:
                logger.warning(f"Error retrieving from Redis: {str(e)}")

        configmap_name = f"{workload_name}-rollback-state"
        try:
            configmap = self.core_v1.read_namespaced_config_map(configmap_name, namespace)
            state_json = configmap.data.get('rollback_state')
            if state_json:
                logger.info(f"Retrieved rollback state from ConfigMap for {workload_kind}/{workload_name}")
                return json.loads(state_json)
        except client.exceptions.ApiException as e:
            if e.status != 404:
                logger.error(f"Error retrieving from ConfigMap: {str(e)}")

        logger.warning(f"No rollback state found for {workload_kind}/{workload_name}")
        return None

    async def _store_in_configmap(
        self,
        namespace: str,
        name: str,
        state: Dict[str, Any]
    ) -> bool:
        try:
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    labels={
                        'app': 'cost-optimizer',
                        'component': 'rollback-state'
                    }
                ),
                data={
                    'rollback_state': json.dumps(state)
                }
            )

            try:
                self.core_v1.create_namespaced_config_map(namespace, configmap)
                logger.info(f"Created ConfigMap {namespace}/{name} for rollback state")
            except client.exceptions.ApiException as e:
                if e.status == 409:
                    self.core_v1.replace_namespaced_config_map(name, namespace, configmap)
                    logger.info(f"Updated ConfigMap {namespace}/{name} for rollback state")
                else:
                    raise

            return True

        except Exception as e:
            logger.error(f"Error storing in ConfigMap: {str(e)}", exc_info=True)
            return False

    def _extract_resources(self, workload) -> Dict[str, str]:
        containers = workload.spec.template.spec.containers
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
