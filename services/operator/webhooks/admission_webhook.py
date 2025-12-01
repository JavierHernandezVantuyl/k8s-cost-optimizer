#!/usr/bin/env python3

import logging
import json
from flask import Flask, request, jsonify
from typing import Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class AdmissionWebhook:

    @staticmethod
    def validate_cost_optimization(obj: Dict[str, Any]) -> Tuple[bool, str]:
        spec = obj.get('spec', {})

        target_workload = spec.get('targetWorkload', {})
        if not target_workload.get('name'):
            return False, "targetWorkload.name is required"

        if not target_workload.get('kind'):
            return False, "targetWorkload.kind is required"

        allowed_kinds = ['Deployment', 'StatefulSet', 'DaemonSet']
        if target_workload.get('kind') not in allowed_kinds:
            return False, f"targetWorkload.kind must be one of {allowed_kinds}"

        optimization_type = spec.get('optimizationType')
        if not optimization_type:
            return False, "optimizationType is required"

        allowed_types = ['CPU', 'MEMORY', 'REPLICAS', 'ALL', 'SPOT_INSTANCES', 'SCHEDULED_SCALING']
        if optimization_type not in allowed_types:
            return False, f"optimizationType must be one of {allowed_types}"

        max_change_percent = spec.get('maxChangePercent', 50)
        if max_change_percent < 1 or max_change_percent > 100:
            return False, "maxChangePercent must be between 1 and 100"

        min_confidence = spec.get('minConfidence', 0.7)
        if min_confidence < 0.0 or min_confidence > 1.0:
            return False, "minConfidence must be between 0.0 and 1.0"

        dry_run = spec.get('dryRun', True)
        auto_apply = spec.get('autoApply', False)

        if auto_apply and dry_run:
            return False, "Cannot enable both autoApply and dryRun"

        max_risk_level = spec.get('maxRiskLevel', 'MEDIUM')
        allowed_risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if max_risk_level not in allowed_risk_levels:
            return False, f"maxRiskLevel must be one of {allowed_risk_levels}"

        if auto_apply and max_risk_level in ['HIGH', 'CRITICAL']:
            return False, "Cannot enable autoApply with maxRiskLevel HIGH or CRITICAL"

        if target_workload.get('kind') == 'StatefulSet' and optimization_type == 'REPLICAS':
            if auto_apply:
                return False, "Cannot auto-apply replica optimization to StatefulSet. Manual intervention required."

        if target_workload.get('kind') == 'DaemonSet' and optimization_type in ['REPLICAS', 'ALL']:
            return False, "Cannot optimize replicas for DaemonSet"

        if optimization_type == 'SPOT_INSTANCES':
            if auto_apply and min_confidence < 0.8:
                return False, "Spot instance optimization requires minConfidence >= 0.8 for auto-apply"

        return True, "Validation passed"

    @staticmethod
    def prevent_dangerous_optimization(obj: Dict[str, Any]) -> Tuple[bool, str]:
        spec = obj.get('spec', {})
        metadata = obj.get('metadata', {})

        namespace = metadata.get('namespace', 'default')
        if namespace in ['kube-system', 'kube-public', 'kube-node-lease']:
            return False, f"Cannot optimize workloads in {namespace} namespace"

        target_workload = spec.get('targetWorkload', {})
        workload_name = target_workload.get('name', '')

        protected_workloads = [
            'kube-dns',
            'coredns',
            'kube-proxy',
            'metrics-server',
            'kubernetes-dashboard'
        ]

        if workload_name in protected_workloads:
            return False, f"Cannot optimize protected workload: {workload_name}"

        labels = metadata.get('labels', {})
        if labels.get('app.kubernetes.io/component') == 'controller':
            return False, "Cannot optimize Kubernetes controller components"

        max_change_percent = spec.get('maxChangePercent', 50)
        if max_change_percent > 80 and spec.get('autoApply', False):
            return False, "Cannot auto-apply optimizations with maxChangePercent > 80%"

        return True, "Safety checks passed"


@app.route('/validate', methods=['POST'])
def validate():
    try:
        admission_review = request.get_json()

        logger.info(f"Received validation request: {admission_review.get('request', {}).get('uid')}")

        req = admission_review.get('request', {})
        obj = req.get('object', {})

        webhook = AdmissionWebhook()

        valid, message = webhook.validate_cost_optimization(obj)
        if not valid:
            logger.warning(f"Validation failed: {message}")
            return jsonify({
                'apiVersion': 'admission.k8s.io/v1',
                'kind': 'AdmissionReview',
                'response': {
                    'uid': req.get('uid'),
                    'allowed': False,
                    'status': {
                        'code': 400,
                        'message': message
                    }
                }
            })

        safe, message = webhook.prevent_dangerous_optimization(obj)
        if not safe:
            logger.warning(f"Safety check failed: {message}")
            return jsonify({
                'apiVersion': 'admission.k8s.io/v1',
                'kind': 'AdmissionReview',
                'response': {
                    'uid': req.get('uid'),
                    'allowed': False,
                    'status': {
                        'code': 403,
                        'message': message
                    }
                }
            })

        logger.info(f"Validation passed for {obj.get('metadata', {}).get('name')}")

        return jsonify({
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': req.get('uid'),
                'allowed': True
            }
        })

    except Exception as e:
        logger.error(f"Error in validation webhook: {str(e)}", exc_info=True)
        return jsonify({
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': request.get_json().get('request', {}).get('uid'),
                'allowed': False,
                'status': {
                    'code': 500,
                    'message': f'Internal error: {str(e)}'
                }
            }
        }), 500


@app.route('/mutate', methods=['POST'])
def mutate():
    try:
        admission_review = request.get_json()

        logger.info(f"Received mutation request: {admission_review.get('request', {}).get('uid')}")

        req = admission_review.get('request', {})
        obj = req.get('object', {})

        patches = []

        if 'status' not in obj:
            patches.append({
                'op': 'add',
                'path': '/status',
                'value': {
                    'phase': 'Pending',
                    'message': 'CostOptimization created',
                    'appliedOptimizations': 0,
                    'totalSavings': 0.0,
                    'conditions': []
                }
            })

        metadata = obj.get('metadata', {})
        if 'labels' not in metadata:
            patches.append({
                'op': 'add',
                'path': '/metadata/labels',
                'value': {}
            })

        patches.append({
            'op': 'add',
            'path': '/metadata/labels/app.kubernetes.io~1managed-by',
            'value': 'cost-optimizer-operator'
        })

        import base64
        patch_json = json.dumps(patches)
        patch_base64 = base64.b64encode(patch_json.encode()).decode()

        logger.info(f"Applying {len(patches)} mutations")

        return jsonify({
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': req.get('uid'),
                'allowed': True,
                'patchType': 'JSONPatch',
                'patch': patch_base64
            }
        })

    except Exception as e:
        logger.error(f"Error in mutation webhook: {str(e)}", exc_info=True)
        return jsonify({
            'apiVersion': 'admission.k8s.io/v1',
            'kind': 'AdmissionReview',
            'response': {
                'uid': request.get_json().get('request', {}).get('uid'),
                'allowed': True
            }
        })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443, ssl_context='adhoc')
