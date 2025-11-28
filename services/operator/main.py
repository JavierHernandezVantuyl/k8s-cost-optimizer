#!/usr/bin/env python3

import kopf
import kubernetes
import logging
import os
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from typing import Optional, Dict, Any

from handlers.optimization_handler import OptimizationHandler
from handlers.workload_handler import WorkloadHandler
from handlers.rollback_handler import RollbackHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OPTIMIZER_API_URL = os.getenv("OPTIMIZER_API_URL", "http://optimizer-api:8000")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8080"))

optimizations_created = Counter(
    'costopt_optimizations_created_total',
    'Total number of CostOptimization resources created'
)
optimizations_applied = Counter(
    'costopt_optimizations_applied_total',
    'Total number of optimizations successfully applied',
    ['optimization_type']
)
optimizations_failed = Counter(
    'costopt_optimizations_failed_total',
    'Total number of failed optimizations',
    ['reason']
)
rollbacks_executed = Counter(
    'costopt_rollbacks_total',
    'Total number of rollbacks executed'
)
total_savings = Gauge(
    'costopt_total_monthly_savings_usd',
    'Total monthly cost savings in USD'
)
optimization_duration = Histogram(
    'costopt_optimization_duration_seconds',
    'Time taken to complete optimization',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

optimization_handler: Optional[OptimizationHandler] = None
workload_handler: Optional[WorkloadHandler] = None
rollback_handler: Optional[RollbackHandler] = None


@kopf.on.startup()
async def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.INFO
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 10 * 60

    start_http_server(PROMETHEUS_PORT)
    logger.info(f"Prometheus metrics server started on port {PROMETHEUS_PORT}")

    global optimization_handler, workload_handler, rollback_handler

    kubernetes.config.load_incluster_config()
    api_client = kubernetes.client.ApiClient()

    optimization_handler = OptimizationHandler(
        api_client=api_client,
        optimizer_api_url=OPTIMIZER_API_URL
    )
    workload_handler = WorkloadHandler(
        api_client=api_client,
        optimizer_api_url=OPTIMIZER_API_URL
    )
    rollback_handler = RollbackHandler(api_client=api_client)

    logger.info("K8s Cost Optimization Operator started successfully")
    logger.info(f"Optimizer API URL: {OPTIMIZER_API_URL}")


@kopf.on.create('optimization.k8s.io', 'v1', 'costoptimizations')
async def create_optimization(spec, name, namespace, status, **kwargs):
    logger.info(f"CostOptimization created: {namespace}/{name}")
    optimizations_created.inc()

    try:
        target = spec.get('targetWorkload', {})
        workload_name = target.get('name')
        workload_kind = target.get('kind')
        workload_namespace = target.get('namespace', namespace)
        optimization_type = spec.get('optimizationType')
        dry_run = spec.get('dryRun', True)
        auto_apply = spec.get('autoApply', False)

        logger.info(
            f"Processing optimization for {workload_kind}/{workload_name} "
            f"in namespace {workload_namespace}"
        )

        kopf.info(
            kwargs['body'],
            reason='OptimizationCreated',
            message=f'Started analyzing {workload_kind}/{workload_name}'
        )

        return {
            'phase': 'Analyzing',
            'message': f'Analyzing {workload_kind}/{workload_name} for {optimization_type} optimization',
            'lastAnalysis': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error creating optimization: {str(e)}", exc_info=True)
        optimizations_failed.labels(reason='creation_error').inc()
        raise kopf.PermanentError(f"Failed to create optimization: {str(e)}")


@kopf.on.update('optimization.k8s.io', 'v1', 'costoptimizations')
async def update_optimization(spec, name, namespace, old, new, **kwargs):
    logger.info(f"CostOptimization updated: {namespace}/{name}")

    old_spec = old.get('spec', {})
    new_spec = new.get('spec', {})

    if old_spec.get('autoApply') != new_spec.get('autoApply'):
        logger.info(f"AutoApply changed for {namespace}/{name}: {new_spec.get('autoApply')}")
        kopf.info(
            kwargs['body'],
            reason='ConfigurationChanged',
            message=f'AutoApply setting changed to {new_spec.get("autoApply")}'
        )

    return {'phase': 'Ready', 'message': 'Configuration updated'}


@kopf.on.delete('optimization.k8s.io', 'v1', 'costoptimizations')
async def delete_optimization(spec, name, namespace, status, **kwargs):
    logger.info(f"CostOptimization deleted: {namespace}/{name}")

    try:
        phase = status.get('phase')

        if phase == 'Applied':
            logger.info(f"Executing rollback for {namespace}/{name}")

            target = spec.get('targetWorkload', {})
            workload_name = target.get('name')
            workload_kind = target.get('kind')
            workload_namespace = target.get('namespace', namespace)

            if spec.get('rollbackOnFailure', True):
                await rollback_handler.execute_rollback(
                    workload_name=workload_name,
                    workload_kind=workload_kind,
                    namespace=workload_namespace
                )
                rollbacks_executed.inc()
                logger.info(f"Rollback completed for {namespace}/{name}")
            else:
                logger.info(f"Rollback disabled for {namespace}/{name}")

        kopf.info(
            kwargs['body'],
            reason='OptimizationDeleted',
            message=f'CostOptimization {name} deleted'
        )

    except Exception as e:
        logger.error(f"Error during deletion: {str(e)}", exc_info=True)


@kopf.timer('optimization.k8s.io', 'v1', 'costoptimizations', interval=1800.0)
async def periodic_optimization_check(spec, name, namespace, status, patch, **kwargs):
    logger.info(f"Periodic check for {namespace}/{name}")

    try:
        target = spec.get('targetWorkload', {})
        workload_name = target.get('name')
        workload_kind = target.get('kind')
        workload_namespace = target.get('namespace', namespace)
        optimization_type = spec.get('optimizationType')
        dry_run = spec.get('dryRun', True)
        auto_apply = spec.get('autoApply', False)
        min_confidence = spec.get('minConfidence', 0.7)
        max_risk_level = spec.get('maxRiskLevel', 'MEDIUM')

        with optimization_duration.time():
            recommendation = await optimization_handler.analyze_workload(
                workload_name=workload_name,
                workload_kind=workload_kind,
                namespace=workload_namespace,
                optimization_type=optimization_type,
                min_confidence=min_confidence
            )

        if not recommendation:
            logger.info(f"No optimization found for {workload_kind}/{workload_name}")
            patch.status['phase'] = 'Ready'
            patch.status['message'] = 'No optimization opportunities found'
            patch.status['lastAnalysis'] = datetime.utcnow().isoformat()
            return

        logger.info(
            f"Found optimization for {workload_kind}/{workload_name}: "
            f"${recommendation.get('monthly_savings', 0):.2f}/month savings"
        )

        patch.status['currentRecommendation'] = {
            'optimizationType': recommendation.get('optimization_type'),
            'currentCost': recommendation.get('current_cost', {}).get('monthly', 0),
            'optimizedCost': recommendation.get('optimized_cost', {}).get('monthly', 0),
            'monthlySavings': recommendation.get('monthly_savings', 0),
            'confidenceScore': recommendation.get('confidence_score', 0),
            'riskLevel': recommendation.get('risk_assessment', {}).get('level', 'UNKNOWN'),
            'changes': recommendation.get('recommended_config', {})
        }
        patch.status['lastAnalysis'] = datetime.utcnow().isoformat()

        risk_level = recommendation.get('risk_assessment', {}).get('level', 'HIGH')
        confidence = recommendation.get('confidence_score', 0)

        risk_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        max_risk = risk_levels.get(max_risk_level, 2)
        current_risk = risk_levels.get(risk_level, 4)

        if auto_apply and not dry_run:
            if confidence >= min_confidence and current_risk <= max_risk:
                logger.info(f"Auto-applying optimization for {workload_kind}/{workload_name}")

                success = await optimization_handler.apply_optimization(
                    workload_name=workload_name,
                    workload_kind=workload_kind,
                    namespace=workload_namespace,
                    recommendation=recommendation,
                    dry_run=False
                )

                if success:
                    optimizations_applied.labels(
                        optimization_type=optimization_type
                    ).inc()

                    current_savings = status.get('totalSavings', 0)
                    new_savings = current_savings + recommendation.get('monthly_savings', 0)
                    total_savings.set(new_savings)

                    patch.status['phase'] = 'Applied'
                    patch.status['message'] = 'Optimization applied successfully'
                    patch.status['lastApplied'] = datetime.utcnow().isoformat()
                    patch.status['appliedOptimizations'] = status.get('appliedOptimizations', 0) + 1
                    patch.status['totalSavings'] = new_savings

                    kopf.info(
                        kwargs['body'],
                        reason='OptimizationApplied',
                        message=f'Applied optimization: ${recommendation.get("monthly_savings", 0):.2f}/month savings'
                    )
                else:
                    optimizations_failed.labels(reason='application_failed').inc()
                    patch.status['phase'] = 'Failed'
                    patch.status['message'] = 'Failed to apply optimization'

                    kopf.warn(
                        kwargs['body'],
                        reason='OptimizationFailed',
                        message='Failed to apply optimization'
                    )
            else:
                logger.info(
                    f"Skipping auto-apply: confidence={confidence:.2f}, "
                    f"risk={risk_level}, max_risk={max_risk_level}"
                )
                patch.status['phase'] = 'Ready'
                patch.status['message'] = (
                    f'Optimization found but not applied: '
                    f'confidence={confidence:.2f}, risk={risk_level}'
                )
        else:
            patch.status['phase'] = 'Ready'
            if dry_run:
                patch.status['message'] = f'Dry-run mode: Would save ${recommendation.get("monthly_savings", 0):.2f}/month'
            else:
                patch.status['message'] = 'Auto-apply disabled'

    except Exception as e:
        logger.error(f"Error in periodic check: {str(e)}", exc_info=True)
        optimizations_failed.labels(reason='periodic_check_error').inc()
        patch.status['phase'] = 'Failed'
        patch.status['message'] = f'Error: {str(e)}'


@kopf.daemon('optimization.k8s.io', 'v1', 'costoptimizations')
async def watch_optimization_status(spec, name, namespace, stopped, **kwargs):
    logger.info(f"Starting status watcher for {namespace}/{name}")

    while not stopped:
        await stopped.wait(60)


@kopf.on.event('', 'v1', 'pods')
async def pod_event_handler(event, name, namespace, **kwargs):
    event_type = event.get('type')

    if event_type in ['MODIFIED', 'DELETED']:
        logger.debug(f"Pod event: {event_type} {namespace}/{name}")


if __name__ == '__main__':
    kopf.run()
