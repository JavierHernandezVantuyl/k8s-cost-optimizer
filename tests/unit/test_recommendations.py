"""
Unit tests for recommendation generation logic.

Tests cover:
- Recommendation prioritization
- Confidence scoring
- Impact estimation
- Risk assessment
- Recommendation filtering
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock


class TestRecommendationGenerator:
    """Test recommendation generation."""

    def test_generate_right_sizing_recommendation(self):
        """Test generating right-sizing recommendation."""
        from services.optimizer_api.recommendations.generator import RecommendationGenerator

        workload_data = {
            'name': 'api-service',
            'namespace': 'production',
            'current': {
                'cpu_request': '1000m',
                'memory_request': '2Gi'
            },
            'usage': {
                'cpu_avg': '300m',
                'cpu_p95': '450m',
                'memory_avg': '800Mi',
                'memory_p95': '1.2Gi'
            }
        }

        generator = RecommendationGenerator()
        recommendation = generator.generate(workload_data, type='right_sizing')

        assert recommendation['type'] == 'right_sizing'
        assert recommendation['workload'] == 'api-service'
        assert 'current' in recommendation
        assert 'recommended' in recommendation
        assert 'savings' in recommendation
        assert recommendation['recommended']['cpu'] < '1000m'

    def test_generate_spot_recommendation(self):
        """Test generating spot instance recommendation."""
        from services.optimizer_api.recommendations.generator import RecommendationGenerator

        workload_data = {
            'name': 'batch-processor',
            'type': 'Job',
            'fault_tolerant': True,
            'current_cost': 500  # $500/month
        }

        generator = RecommendationGenerator()
        recommendation = generator.generate(workload_data, type='spot_instance')

        assert recommendation['type'] == 'spot_instance'
        assert recommendation['estimated_savings'] > 0
        assert recommendation['estimated_savings_percent'] > 50
        assert 'interruption_handling' in recommendation

    def test_generate_hpa_recommendation(self):
        """Test generating HPA (autoscaling) recommendation."""
        from services.optimizer_api.recommendations.generator import RecommendationGenerator

        workload_data = {
            'name': 'web-app',
            'current_replicas': 5,
            'usage_pattern': 'variable',
            'peak_usage': '80%',
            'off_peak_usage': '20%'
        }

        generator = RecommendationGenerator()
        recommendation = generator.generate(workload_data, type='horizontal_scaling')

        assert recommendation['type'] == 'horizontal_scaling'
        assert 'min_replicas' in recommendation['recommended']
        assert 'max_replicas' in recommendation['recommended']
        assert 'target_cpu_utilization' in recommendation['recommended']


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_high_confidence_with_sufficient_data(self):
        """Test high confidence when enough historical data exists."""
        from services.optimizer_api.recommendations.scoring import ConfidenceScorer

        data = {
            'metrics_duration_days': 30,
            'data_points': 720,  # 30 days * 24 hours
            'data_completeness': 0.98,  # 98% complete
            'variance': 0.15  # Low variance
        }

        scorer = ConfidenceScorer()
        confidence = scorer.calculate(data)

        assert confidence >= 0.8  # High confidence
        assert confidence <= 1.0

    def test_low_confidence_with_insufficient_data(self):
        """Test low confidence with limited data."""
        from services.optimizer_api.recommendations.scoring import ConfidenceScorer

        data = {
            'metrics_duration_days': 2,  # Only 2 days
            'data_points': 48,
            'data_completeness': 0.60,  # Missing data
            'variance': 0.45  # High variance
        }

        scorer = ConfidenceScorer()
        confidence = scorer.calculate(data)

        assert confidence < 0.5  # Low confidence

    def test_medium_confidence_with_gaps(self):
        """Test medium confidence with data gaps."""
        from services.optimizer_api.recommendations.scoring import ConfidenceScorer

        data = {
            'metrics_duration_days': 14,
            'data_points': 336,
            'data_completeness': 0.75,  # Some gaps
            'variance': 0.25
        }

        scorer = ConfidenceScorer()
        confidence = scorer.calculate(data)

        assert 0.5 <= confidence < 0.8  # Medium confidence


class TestImpactEstimation:
    """Test impact estimation for recommendations."""

    def test_financial_impact(self):
        """Test estimating financial impact."""
        from services.optimizer_api.recommendations.impact import ImpactEstimator

        recommendation = {
            'type': 'right_sizing',
            'current_cost': 1000,  # $1000/month
            'optimized_cost': 600  # $600/month
        }

        estimator = ImpactEstimator()
        impact = estimator.estimate_financial(recommendation)

        assert impact['monthly_savings'] == 400
        assert impact['annual_savings'] == 4800
        assert impact['savings_percent'] == 40

    def test_performance_impact(self):
        """Test estimating performance impact."""
        from services.optimizer_api.recommendations.impact import ImpactEstimator

        recommendation = {
            'type': 'right_sizing',
            'current': {'cpu': '2000m', 'memory': '4Gi'},
            'recommended': {'cpu': '1000m', 'memory': '2Gi'},
            'p95_usage': {'cpu': '800m', 'memory': '1.5Gi'}
        }

        estimator = ImpactEstimator()
        impact = estimator.estimate_performance(recommendation)

        assert impact['risk_level'] in ['low', 'medium', 'high']
        assert 'headroom_percent' in impact
        assert impact['risk_level'] == 'low'  # Plenty of headroom

    def test_availability_impact(self):
        """Test estimating availability impact."""
        from services.optimizer_api.recommendations.impact import ImpactEstimator

        recommendation = {
            'type': 'spot_instance',
            'workload_criticality': 'high',
            'sla_requirement': '99.9%',
            'estimated_interruption_rate': 0.05  # 5%
        }

        estimator = ImpactEstimator()
        impact = estimator.estimate_availability(recommendation)

        assert impact['risk_level'] == 'high'  # High criticality + spot = high risk
        assert 'mitigation_strategies' in impact


class TestRiskAssessment:
    """Test risk assessment for recommendations."""

    def test_low_risk_recommendation(self):
        """Test identifying low-risk recommendation."""
        from services.optimizer_api.recommendations.risk import RiskAssessor

        recommendation = {
            'type': 'right_sizing',
            'reduction_percent': 20,  # Minor reduction
            'confidence': 0.9,  # High confidence
            'workload_type': 'batch',
            'has_hpa': True  # Can auto-scale if needed
        }

        assessor = RiskAssessor()
        risk = assessor.assess(recommendation)

        assert risk['level'] == 'low'
        assert risk['score'] < 0.3

    def test_high_risk_recommendation(self):
        """Test identifying high-risk recommendation."""
        from services.optimizer_api.recommendations.risk import RiskAssessor

        recommendation = {
            'type': 'spot_instance',
            'workload_type': 'stateful_database',
            'sla_requirement': '99.99%',
            'confidence': 0.6,  # Medium confidence
            'current_uptime': '99.95%'
        }

        assessor = RiskAssessor()
        risk = assessor.assess(recommendation)

        assert risk['level'] == 'high'
        assert risk['score'] > 0.7
        assert len(risk['concerns']) > 0

    def test_risk_mitigation_suggestions(self):
        """Test risk mitigation suggestions."""
        from services.optimizer_api.recommendations.risk import RiskAssessor

        recommendation = {
            'type': 'aggressive_right_sizing',
            'reduction_percent': 60,
            'confidence': 0.7
        }

        assessor = RiskAssessor()
        risk = assessor.assess(recommendation)

        assert 'mitigation_strategies' in risk
        # Should suggest gradual rollout
        assert any('gradual' in s.lower() for s in risk['mitigation_strategies'])


class TestRecommendationPrioritization:
    """Test recommendation prioritization."""

    def test_prioritize_by_savings(self):
        """Test prioritizing recommendations by potential savings."""
        from services.optimizer_api.recommendations.prioritizer import RecommendationPrioritizer

        recommendations = [
            {'id': 1, 'monthly_savings': 100, 'confidence': 0.8, 'risk': 'low'},
            {'id': 2, 'monthly_savings': 1000, 'confidence': 0.9, 'risk': 'low'},
            {'id': 3, 'monthly_savings': 500, 'confidence': 0.7, 'risk': 'medium'}
        ]

        prioritizer = RecommendationPrioritizer(strategy='savings')
        prioritized = prioritizer.prioritize(recommendations)

        # Should be ordered by savings (descending)
        assert prioritized[0]['id'] == 2  # $1000 savings
        assert prioritized[1]['id'] == 3  # $500 savings
        assert prioritized[2]['id'] == 1  # $100 savings

    def test_prioritize_by_roi(self):
        """Test prioritizing by ROI (savings / effort)."""
        from services.optimizer_api.recommendations.prioritizer import RecommendationPrioritizer

        recommendations = [
            {'id': 1, 'monthly_savings': 1000, 'effort': 'high', 'confidence': 0.8},
            {'id': 2, 'monthly_savings': 500, 'effort': 'low', 'confidence': 0.9},
            {'id': 3, 'monthly_savings': 300, 'effort': 'low', 'confidence': 0.85}
        ]

        prioritizer = RecommendationPrioritizer(strategy='roi')
        prioritized = prioritizer.prioritize(recommendations)

        # Low effort + good savings should rank high
        assert prioritized[0]['id'] == 2

    def test_prioritize_by_risk_adjusted(self):
        """Test risk-adjusted prioritization."""
        from services.optimizer_api.recommendations.prioritizer import RecommendationPrioritizer

        recommendations = [
            {'id': 1, 'monthly_savings': 2000, 'risk': 'high', 'confidence': 0.6},
            {'id': 2, 'monthly_savings': 800, 'risk': 'low', 'confidence': 0.9},
            {'id': 3, 'monthly_savings': 1200, 'risk': 'medium', 'confidence': 0.8}
        ]

        prioritizer = RecommendationPrioritizer(strategy='risk_adjusted')
        prioritized = prioritizer.prioritize(recommendations)

        # Lower risk recommendations should rank higher despite lower savings
        assert prioritized[0]['id'] == 2  # Low risk


class TestRecommendationFiltering:
    """Test recommendation filtering."""

    def test_filter_by_confidence_threshold(self):
        """Test filtering out low-confidence recommendations."""
        from services.optimizer_api.recommendations.filter import RecommendationFilter

        recommendations = [
            {'id': 1, 'confidence': 0.9},
            {'id': 2, 'confidence': 0.5},
            {'id': 3, 'confidence': 0.7}
        ]

        filter = RecommendationFilter(min_confidence=0.6)
        filtered = filter.apply(recommendations)

        assert len(filtered) == 2
        assert all(r['confidence'] >= 0.6 for r in filtered)

    def test_filter_by_minimum_savings(self):
        """Test filtering out low-impact recommendations."""
        from services.optimizer_api.recommendations.filter import RecommendationFilter

        recommendations = [
            {'id': 1, 'monthly_savings': 1000},
            {'id': 2, 'monthly_savings': 10},
            {'id': 3, 'monthly_savings': 500}
        ]

        filter = RecommendationFilter(min_monthly_savings=100)
        filtered = filter.apply(recommendations)

        assert len(filtered) == 2
        assert all(r['monthly_savings'] >= 100 for r in filtered)

    def test_filter_by_namespace(self):
        """Test filtering recommendations by namespace."""
        from services.optimizer_api.recommendations.filter import RecommendationFilter

        recommendations = [
            {'id': 1, 'namespace': 'production'},
            {'id': 2, 'namespace': 'staging'},
            {'id': 3, 'namespace': 'production'}
        ]

        filter = RecommendationFilter(namespaces=['production'])
        filtered = filter.apply(recommendations)

        assert len(filtered) == 2
        assert all(r['namespace'] == 'production' for r in filtered)


class TestRecommendationGrouping:
    """Test grouping related recommendations."""

    def test_group_by_workload(self):
        """Test grouping recommendations by workload."""
        from services.optimizer_api.recommendations.grouper import RecommendationGrouper

        recommendations = [
            {'id': 1, 'workload': 'api', 'type': 'right_sizing'},
            {'id': 2, 'workload': 'api', 'type': 'hpa'},
            {'id': 3, 'workload': 'worker', 'type': 'spot'}
        ]

        grouper = RecommendationGrouper()
        grouped = grouper.group_by('workload', recommendations)

        assert 'api' in grouped
        assert 'worker' in grouped
        assert len(grouped['api']) == 2
        assert len(grouped['worker']) == 1

    def test_group_by_type(self):
        """Test grouping recommendations by type."""
        from services.optimizer_api.recommendations.grouper import RecommendationGrouper

        recommendations = [
            {'id': 1, 'type': 'right_sizing', 'savings': 100},
            {'id': 2, 'type': 'right_sizing', 'savings': 200},
            {'id': 3, 'type': 'spot', 'savings': 500},
            {'id': 4, 'type': 'hpa', 'savings': 150}
        ]

        grouper = RecommendationGrouper()
        grouped = grouper.group_by('type', recommendations)

        assert len(grouped['right_sizing']) == 2
        assert len(grouped['spot']) == 1

    def test_aggregate_grouped_savings(self):
        """Test aggregating savings within groups."""
        from services.optimizer_api.recommendations.grouper import RecommendationGrouper

        recommendations = [
            {'id': 1, 'type': 'right_sizing', 'monthly_savings': 100},
            {'id': 2, 'type': 'right_sizing', 'monthly_savings': 200},
            {'id': 3, 'type': 'spot', 'monthly_savings': 500}
        ]

        grouper = RecommendationGrouper()
        grouped = grouper.group_by('type', recommendations)
        aggregated = grouper.aggregate_savings(grouped)

        assert aggregated['right_sizing']['total_monthly_savings'] == 300
        assert aggregated['right_sizing']['count'] == 2
        assert aggregated['spot']['total_monthly_savings'] == 500


class TestRecommendationValidation:
    """Test recommendation validation."""

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        from services.optimizer_api.recommendations.validator import RecommendationValidator

        recommendation = {
            'type': 'right_sizing',
            'workload': 'api',
            'current': {'cpu': '1000m'},
            'recommended': {'cpu': '500m'}
            # Missing: confidence, savings, risk
        }

        validator = RecommendationValidator()
        result = validator.validate(recommendation)

        assert result['valid'] is False
        assert 'missing_fields' in result
        assert 'confidence' in result['missing_fields']

    def test_validate_logical_consistency(self):
        """Test validation of logical consistency."""
        from services.optimizer_api.recommendations.validator import RecommendationValidator

        recommendation = {
            'type': 'right_sizing',
            'current_cost': 100,
            'optimized_cost': 150,  # Optimized is MORE expensive!
            'monthly_savings': 50  # But claims savings?
        }

        validator = RecommendationValidator()
        result = validator.validate(recommendation)

        assert result['valid'] is False
        assert 'inconsistencies' in result

    def test_validate_value_ranges(self):
        """Test validation of value ranges."""
        from services.optimizer_api.recommendations.validator import RecommendationValidator

        recommendation = {
            'type': 'right_sizing',
            'confidence': 1.5,  # Should be 0-1
            'risk_score': -0.2,  # Should be positive
            'savings_percent': 150  # Can't save more than 100%
        }

        validator = RecommendationValidator()
        result = validator.validate(recommendation)

        assert result['valid'] is False
        assert len(result['errors']) >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
