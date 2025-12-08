"""
Unit tests for cost calculation logic.

Tests cover:
- Instance cost calculations
- Storage cost calculations
- Network cost calculations
- Total cost aggregation
- Cost allocation by namespace/label
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class TestInstanceCostCalculator:
    """Test instance cost calculation."""

    def test_on_demand_instance_cost(self):
        """Test calculating on-demand instance cost."""
        from services.optimizer_api.cost.calculator import InstanceCostCalculator

        calculator = InstanceCostCalculator()

        cost = calculator.calculate_cost(
            instance_type='t3.medium',
            cloud='aws',
            region='us-east-1',
            pricing_model='on-demand',
            hours=730  # ~1 month
        )

        # t3.medium is ~$0.0416/hour
        expected = 0.0416 * 730
        assert cost == pytest.approx(expected, 0.01)

    def test_spot_instance_cost(self):
        """Test calculating spot instance cost."""
        from services.optimizer_api.cost.calculator import InstanceCostCalculator

        calculator = InstanceCostCalculator()

        cost = calculator.calculate_cost(
            instance_type='t3.medium',
            cloud='aws',
            region='us-east-1',
            pricing_model='spot',
            hours=730
        )

        # Spot should be significantly cheaper
        on_demand_cost = 0.0416 * 730
        assert cost < on_demand_cost * 0.5  # At least 50% cheaper

    def test_reserved_instance_cost(self):
        """Test calculating reserved instance cost."""
        from services.optimizer_api.cost.calculator import InstanceCostCalculator

        calculator = InstanceCostCalculator()

        # 1-year partial upfront
        cost = calculator.calculate_cost(
            instance_type='t3.medium',
            cloud='aws',
            region='us-east-1',
            pricing_model='reserved',
            reservation_term='1year',
            payment_option='partial_upfront',
            hours=8760  # 1 year
        )

        on_demand_cost = 0.0416 * 8760
        # Reserved should be ~30-40% cheaper
        assert cost < on_demand_cost * 0.7

    def test_multi_region_cost(self):
        """Test costs across different regions."""
        from services.optimizer_api.cost.calculator import InstanceCostCalculator

        calculator = InstanceCostCalculator()

        us_cost = calculator.calculate_cost(
            instance_type='t3.medium',
            cloud='aws',
            region='us-east-1',
            pricing_model='on-demand',
            hours=730
        )

        ap_cost = calculator.calculate_cost(
            instance_type='t3.medium',
            cloud='aws',
            region='ap-southeast-1',
            pricing_model='on-demand',
            hours=730
        )

        # Asia Pacific is typically more expensive
        assert ap_cost > us_cost


class TestStorageCostCalculator:
    """Test storage cost calculation."""

    def test_ebs_volume_cost(self):
        """Test calculating EBS volume cost."""
        from services.optimizer_api.cost.calculator import StorageCostCalculator

        calculator = StorageCostCalculator()

        cost = calculator.calculate_cost(
            storage_type='gp3',
            cloud='aws',
            region='us-east-1',
            size_gb=100,
            days=30
        )

        # gp3 is ~$0.08/GB-month
        expected = 100 * 0.08
        assert cost == pytest.approx(expected, 0.01)

    def test_snapshot_cost(self):
        """Test calculating snapshot costs."""
        from services.optimizer_api.cost.calculator import StorageCostCalculator

        calculator = StorageCostCalculator()

        cost = calculator.calculate_cost(
            storage_type='snapshot',
            cloud='aws',
            region='us-east-1',
            size_gb=50,
            days=30
        )

        # Snapshots are ~$0.05/GB-month
        expected = 50 * 0.05
        assert cost == pytest.approx(expected, 0.01)

    def test_storage_tiering_savings(self):
        """Test cost savings from storage tiering."""
        from services.optimizer_api.cost.calculator import StorageCostCalculator

        calculator = StorageCostCalculator()

        # Standard storage
        standard_cost = calculator.calculate_cost(
            storage_type='gp3',
            cloud='aws',
            region='us-east-1',
            size_gb=1000,
            days=30
        )

        # Infrequent access storage
        ia_cost = calculator.calculate_cost(
            storage_type='sc1',  # Cold HDD
            cloud='aws',
            region='us-east-1',
            size_gb=1000,
            days=30
        )

        # Cold storage should be ~50% cheaper
        assert ia_cost < standard_cost * 0.6


class TestNetworkCostCalculator:
    """Test network cost calculation."""

    def test_data_transfer_out_cost(self):
        """Test calculating data transfer out costs."""
        from services.optimizer_api.cost.calculator import NetworkCostCalculator

        calculator = NetworkCostCalculator()

        cost = calculator.calculate_cost(
            transfer_type='internet',
            cloud='aws',
            region='us-east-1',
            data_gb=1000,  # 1TB
            direction='out'
        )

        # First 1GB free, then tiered pricing
        # Approximately $0.09/GB for first 10TB
        assert cost > 90  # 1000GB * $0.09
        assert cost < 100

    def test_inter_region_transfer_cost(self):
        """Test calculating inter-region transfer costs."""
        from services.optimizer_api.cost.calculator import NetworkCostCalculator

        calculator = NetworkCostCalculator()

        cost = calculator.calculate_cost(
            transfer_type='inter_region',
            cloud='aws',
            source_region='us-east-1',
            dest_region='eu-west-1',
            data_gb=500
        )

        # Inter-region typically $0.02/GB
        expected = 500 * 0.02
        assert cost == pytest.approx(expected, 0.01)

    def test_no_charge_for_incoming(self):
        """Test that incoming data transfer is free."""
        from services.optimizer_api.cost.calculator import NetworkCostCalculator

        calculator = NetworkCostCalculator()

        cost = calculator.calculate_cost(
            transfer_type='internet',
            cloud='aws',
            region='us-east-1',
            data_gb=1000,
            direction='in'
        )

        assert cost == 0


class TestCostAggregator:
    """Test cost aggregation and totals."""

    def test_total_cluster_cost(self):
        """Test calculating total cluster cost."""
        from services.optimizer_api.cost.calculator import CostAggregator

        resources = {
            'instances': [
                {'type': 't3.medium', 'count': 5, 'hours': 730},
                {'type': 't3.large', 'count': 2, 'hours': 730}
            ],
            'storage': [
                {'type': 'gp3', 'size_gb': 500},
                {'type': 'gp3', 'size_gb': 1000}
            ],
            'network': {
                'egress_gb': 2000
            }
        }

        aggregator = CostAggregator()
        total = aggregator.calculate_total(resources, cloud='aws', region='us-east-1')

        assert 'compute_cost' in total
        assert 'storage_cost' in total
        assert 'network_cost' in total
        assert 'total_cost' in total

        # Total should be sum of components
        assert total['total_cost'] == (
            total['compute_cost'] +
            total['storage_cost'] +
            total['network_cost']
        )

    def test_cost_breakdown_by_namespace(self):
        """Test cost allocation by Kubernetes namespace."""
        from services.optimizer_api.cost.calculator import CostAggregator

        resources = [
            {'namespace': 'production', 'cpu': 10, 'memory': 32},
            {'namespace': 'production', 'cpu': 5, 'memory': 16},
            {'namespace': 'staging', 'cpu': 2, 'memory': 8},
            {'namespace': 'dev', 'cpu': 1, 'memory': 4}
        ]

        aggregator = CostAggregator()
        breakdown = aggregator.breakdown_by_namespace(resources)

        assert 'production' in breakdown
        assert 'staging' in breakdown
        assert 'dev' in breakdown

        # Production should be most expensive
        assert breakdown['production']['cost'] > breakdown['staging']['cost']
        assert breakdown['production']['cost'] > breakdown['dev']['cost']

    def test_cost_allocation_by_label(self):
        """Test cost allocation by custom labels."""
        from services.optimizer_api.cost.calculator import CostAggregator

        resources = [
            {'team': 'backend', 'cost': 1000},
            {'team': 'backend', 'cost': 500},
            {'team': 'frontend', 'cost': 750},
            {'team': 'ml', 'cost': 2000}
        ]

        aggregator = CostAggregator()
        breakdown = aggregator.breakdown_by_label(resources, label='team')

        assert breakdown['backend']['total'] == 1500
        assert breakdown['frontend']['total'] == 750
        assert breakdown['ml']['total'] == 2000


class TestHistoricalCostAnalyzer:
    """Test historical cost analysis."""

    def test_daily_cost_trend(self):
        """Test analyzing daily cost trends."""
        from services.optimizer_api.cost.analyzer import HistoricalCostAnalyzer

        # Generate 30 days of cost data
        costs = []
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            # Simulate increasing costs
            daily_cost = 1000 + (i * 10)
            costs.append({'date': date, 'cost': daily_cost})

        analyzer = HistoricalCostAnalyzer()
        trend = analyzer.analyze_trend(costs)

        assert trend['direction'] == 'increasing'
        assert trend['daily_increase'] > 0
        assert 'forecast_30_days' in trend

    def test_cost_anomaly_detection(self):
        """Test detecting cost anomalies."""
        from services.optimizer_api.cost.analyzer import HistoricalCostAnalyzer

        # Normal costs around $1000/day, then spike
        costs = []
        for i in range(30):
            date = datetime.now() - timedelta(days=30-i)
            if i == 25:  # Anomaly on day 25
                daily_cost = 3000  # 3x normal
            else:
                daily_cost = 1000
            costs.append({'date': date, 'cost': daily_cost})

        analyzer = HistoricalCostAnalyzer()
        anomalies = analyzer.detect_anomalies(costs)

        assert len(anomalies) == 1
        assert anomalies[0]['date'].day == (datetime.now() - timedelta(days=5)).day
        assert anomalies[0]['severity'] == 'high'

    def test_month_over_month_comparison(self):
        """Test month-over-month cost comparison."""
        from services.optimizer_api.cost.analyzer import HistoricalCostAnalyzer

        current_month = 45000  # $45k
        previous_month = 40000  # $40k

        analyzer = HistoricalCostAnalyzer()
        comparison = analyzer.compare_months(current_month, previous_month)

        assert comparison['change_amount'] == 5000
        assert comparison['change_percent'] == 12.5
        assert comparison['trend'] == 'increase'


class TestCostForecast:
    """Test cost forecasting."""

    def test_linear_forecast(self):
        """Test linear regression forecast."""
        from services.optimizer_api.cost.forecast import CostForecaster

        # Historical costs with linear growth
        historical = [
            {'date': datetime(2024, 1, 1), 'cost': 10000},
            {'date': datetime(2024, 2, 1), 'cost': 11000},
            {'date': datetime(2024, 3, 1), 'cost': 12000},
            {'date': datetime(2024, 4, 1), 'cost': 13000}
        ]

        forecaster = CostForecaster(method='linear')
        forecast = forecaster.forecast(historical, periods=3)

        # Should predict ~14000, 15000, 16000
        assert len(forecast) == 3
        assert forecast[0]['cost'] == pytest.approx(14000, 100)
        assert forecast[1]['cost'] == pytest.approx(15000, 100)

    def test_seasonal_forecast(self):
        """Test seasonal forecast for cyclical patterns."""
        from services.optimizer_api.cost.forecast import CostForecaster
        import numpy as np

        # Create seasonal pattern (e.g., higher on weekdays)
        historical = []
        for i in range(90):  # 90 days
            date = datetime.now() - timedelta(days=90-i)
            # Higher cost on weekdays
            if date.weekday() < 5:
                cost = 1500
            else:
                cost = 800
            historical.append({'date': date, 'cost': cost})

        forecaster = CostForecaster(method='seasonal')
        forecast = forecaster.forecast(historical, periods=7)

        # Should predict higher costs for weekdays
        weekday_forecast = [f for f in forecast if f['date'].weekday() < 5]
        weekend_forecast = [f for f in forecast if f['date'].weekday() >= 5]

        avg_weekday = np.mean([f['cost'] for f in weekday_forecast])
        avg_weekend = np.mean([f['cost'] for f in weekend_forecast])

        assert avg_weekday > avg_weekend


class TestBudgetAlerts:
    """Test budget alert system."""

    def test_budget_threshold_alert(self):
        """Test alerting when budget threshold is exceeded."""
        from services.optimizer_api.cost.alerts import BudgetAlertSystem

        budget = {
            'monthly_limit': 50000,
            'thresholds': [0.5, 0.75, 0.9, 1.0]  # Alert at 50%, 75%, 90%, 100%
        }

        alert_system = BudgetAlertSystem(budget)

        # Spend 40k (80% of budget)
        alert = alert_system.check_spending(40000)

        assert alert is not None
        assert alert['threshold'] == 0.75
        assert alert['percent_used'] == 80
        assert alert['severity'] == 'warning'

    def test_spend_rate_alert(self):
        """Test alerting based on spending rate."""
        from services.optimizer_api.cost.alerts import BudgetAlertSystem

        budget = {'monthly_limit': 30000}

        # Day 10 of month, spent $15000
        # Rate: $1500/day, projected: $45000/month (exceeds budget)

        alert_system = BudgetAlertSystem(budget)
        alert = alert_system.check_spend_rate(
            current_spend=15000,
            days_elapsed=10
        )

        assert alert is not None
        assert alert['projected_spend'] > 30000
        assert alert['type'] == 'spend_rate'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
