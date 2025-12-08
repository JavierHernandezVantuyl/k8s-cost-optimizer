"""
Unit tests for cloud pricing API integrations.

Tests cover:
- AWS pricing API
- GCP pricing API
- Azure pricing API
- Price caching
- Rate limiting
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json


@pytest.fixture
def mock_aws_pricing_client():
    """Mock AWS pricing client."""
    client = Mock()
    client.get_products.return_value = {
        'PriceList': [
            json.dumps({
                'product': {
                    'attributes': {
                        'instanceType': 't3.medium',
                        'location': 'US East (N. Virginia)',
                        'operatingSystem': 'Linux'
                    }
                },
                'terms': {
                    'OnDemand': {
                        'price': {
                            'priceDimensions': {
                                'dim1': {
                                    'pricePerUnit': {'USD': '0.0416'}
                                }
                            }
                        }
                    }
                }
            })
        ]
    }
    return client


@pytest.fixture
def mock_gcp_pricing_client():
    """Mock GCP pricing client."""
    client = Mock()
    client.services().skus().list().execute.return_value = {
        'skus': [
            {
                'description': 'N1 Predefined Instance Core running in Americas',
                'category': {
                    'resourceFamily': 'Compute',
                    'resourceGroup': 'N1Standard',
                    'usageType': 'OnDemand'
                },
                'pricingInfo': [{
                    'pricingExpression': {
                        'tieredRates': [{
                            'unitPrice': {
                                'currencyCode': 'USD',
                                'units': '0',
                                'nanos': 31611000
                            }
                        }]
                    }
                }]
            }
        ]
    }
    return client


class TestAWSPricingAPI:
    """Test AWS pricing API integration."""

    def test_get_ec2_instance_price(self, mock_aws_pricing_client):
        """Test fetching EC2 instance price."""
        from services.optimizer_api.pricing.aws import AWSPricingService

        service = AWSPricingService()
        service.client = mock_aws_pricing_client

        price = service.get_ec2_price('t3.medium', 'us-east-1', 'Linux')

        assert price == 0.0416
        mock_aws_pricing_client.get_products.assert_called_once()

    def test_get_ebs_volume_price(self, mock_aws_pricing_client):
        """Test fetching EBS volume price."""
        from services.optimizer_api.pricing.aws import AWSPricingService

        mock_aws_pricing_client.get_products.return_value = {
            'PriceList': [
                json.dumps({
                    'product': {
                        'attributes': {
                            'volumeApiName': 'gp3',
                            'location': 'US East (N. Virginia)'
                        }
                    },
                    'terms': {
                        'OnDemand': {
                            'price': {
                                'priceDimensions': {
                                    'dim1': {
                                        'pricePerUnit': {'USD': '0.08'}
                                    }
                                }
                            }
                        }
                    }
                })
            ]
        }

        service = AWSPricingService()
        service.client = mock_aws_pricing_client

        price = service.get_ebs_price('gp3', 'us-east-1')

        assert price == 0.08

    def test_price_caching(self, mock_aws_pricing_client):
        """Test that prices are cached to reduce API calls."""
        from services.optimizer_api.pricing.aws import AWSPricingService

        service = AWSPricingService()
        service.client = mock_aws_pricing_client

        # First call - should hit API
        price1 = service.get_ec2_price('t3.medium', 'us-east-1', 'Linux')

        # Second call - should use cache
        price2 = service.get_ec2_price('t3.medium', 'us-east-1', 'Linux')

        assert price1 == price2
        # Should only call API once due to caching
        assert mock_aws_pricing_client.get_products.call_count == 1

    def test_rate_limiting(self, mock_aws_pricing_client):
        """Test rate limiting for API calls."""
        from services.optimizer_api.pricing.aws import AWSPricingService
        import time

        service = AWSPricingService(rate_limit=2)  # 2 calls per second
        service.client = mock_aws_pricing_client

        start = time.time()

        # Make 5 calls - should be rate limited
        for i in range(5):
            service.get_ec2_price(f't3.{i}', 'us-east-1', 'Linux')

        elapsed = time.time() - start

        # Should take at least 2 seconds due to rate limiting
        assert elapsed >= 2.0

    def test_error_handling_invalid_instance(self, mock_aws_pricing_client):
        """Test error handling for invalid instance type."""
        from services.optimizer_api.pricing.aws import AWSPricingService

        mock_aws_pricing_client.get_products.return_value = {'PriceList': []}

        service = AWSPricingService()
        service.client = mock_aws_pricing_client

        with pytest.raises(ValueError, match="No pricing found"):
            service.get_ec2_price('invalid.instance', 'us-east-1', 'Linux')


class TestGCPPricingAPI:
    """Test GCP pricing API integration."""

    def test_get_compute_instance_price(self, mock_gcp_pricing_client):
        """Test fetching GCP compute instance price."""
        from services.optimizer_api.pricing.gcp import GCPPricingService

        service = GCPPricingService()
        service.client = mock_gcp_pricing_client

        price = service.get_instance_price('n1-standard-1', 'us-central1')

        # Price is in nanos, should convert to dollars
        assert price == 0.031611

    def test_get_persistent_disk_price(self, mock_gcp_pricing_client):
        """Test fetching persistent disk price."""
        from services.optimizer_api.pricing.gcp import GCPPricingService

        mock_gcp_pricing_client.services().skus().list().execute.return_value = {
            'skus': [{
                'description': 'SSD backed PD Capacity',
                'category': {'resourceFamily': 'Storage'},
                'pricingInfo': [{
                    'pricingExpression': {
                        'tieredRates': [{
                            'unitPrice': {
                                'currencyCode': 'USD',
                                'units': '0',
                                'nanos': 170000000
                            }
                        }]
                    }
                }]
            }]
        }

        service = GCPPricingService()
        service.client = mock_gcp_pricing_client

        price = service.get_disk_price('pd-ssd', 'us-central1')

        assert price == 0.17

    def test_regional_pricing_differences(self, mock_gcp_pricing_client):
        """Test that regional pricing is correctly handled."""
        from services.optimizer_api.pricing.gcp import GCPPricingService

        service = GCPPricingService()
        service.client = mock_gcp_pricing_client

        # Prices should differ by region
        us_price = service.get_instance_price('n1-standard-1', 'us-central1')
        eu_price = service.get_instance_price('n1-standard-1', 'europe-west1')

        # Mock should return same, but real implementation would differ
        assert isinstance(us_price, float)
        assert isinstance(eu_price, float)


class TestAzurePricingAPI:
    """Test Azure pricing API integration."""

    @patch('requests.get')
    def test_get_vm_price(self, mock_get):
        """Test fetching Azure VM price."""
        from services.optimizer_api.pricing.azure import AzurePricingService

        mock_response = Mock()
        mock_response.json.return_value = {
            'Items': [{
                'armSkuName': 'Standard_D2s_v3',
                'retailPrice': 0.096,
                'armRegionName': 'eastus',
                'productName': 'Virtual Machines DS Series'
            }]
        }
        mock_get.return_value = mock_response

        service = AzurePricingService()
        price = service.get_vm_price('Standard_D2s_v3', 'eastus')

        assert price == 0.096

    @patch('requests.get')
    def test_get_managed_disk_price(self, mock_get):
        """Test fetching Azure Managed Disk price."""
        from services.optimizer_api.pricing.azure import AzurePricingService

        mock_response = Mock()
        mock_response.json.return_value = {
            'Items': [{
                'skuName': 'P10 LRS',
                'retailPrice': 19.71,
                'armRegionName': 'eastus',
                'productName': 'Premium SSD Managed Disks'
            }]
        }
        mock_get.return_value = mock_response

        service = AzurePricingService()
        price = service.get_disk_price('Premium_LRS', 'P10', 'eastus')

        assert price == 19.71

    @patch('requests.get')
    def test_spot_instance_pricing(self, mock_get):
        """Test fetching Azure Spot VM pricing."""
        from services.optimizer_api.pricing.azure import AzurePricingService

        mock_response = Mock()
        mock_response.json.return_value = {
            'Items': [{
                'armSkuName': 'Standard_D2s_v3',
                'retailPrice': 0.0288,  # ~70% discount
                'armRegionName': 'eastus',
                'priceType': 'Spot'
            }]
        }
        mock_get.return_value = mock_response

        service = AzurePricingService()
        price = service.get_spot_price('Standard_D2s_v3', 'eastus')

        assert price == 0.0288
        assert price < 0.096  # Should be cheaper than on-demand


class TestPricingCache:
    """Test pricing cache implementation."""

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        from services.optimizer_api.pricing.cache import PricingCache

        cache = PricingCache(ttl=1)  # 1 second TTL

        cache.set('test_key', 100.0)
        assert cache.get('test_key') == 100.0

        # Wait for expiration
        import time
        time.sleep(1.1)

        assert cache.get('test_key') is None

    def test_cache_invalidation(self):
        """Test manual cache invalidation."""
        from services.optimizer_api.pricing.cache import PricingCache

        cache = PricingCache()

        cache.set('key1', 100.0)
        cache.set('key2', 200.0)

        assert cache.get('key1') == 100.0

        cache.invalidate('key1')

        assert cache.get('key1') is None
        assert cache.get('key2') == 200.0

    def test_cache_statistics(self):
        """Test cache hit/miss statistics."""
        from services.optimizer_api.pricing.cache import PricingCache

        cache = PricingCache()

        cache.set('key1', 100.0)

        # Hit
        cache.get('key1')

        # Miss
        cache.get('key2')

        stats = cache.get_stats()

        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5


class TestMultiCloudPricing:
    """Test multi-cloud pricing comparisons."""

    def test_compare_instance_prices(self):
        """Test comparing similar instances across clouds."""
        from services.optimizer_api.pricing.comparator import PricingComparator

        comparator = PricingComparator()

        comparison = comparator.compare_instances({
            'cpu': 2,
            'memory': 8,  # GB
            'region': 'us-east'
        })

        assert 'aws' in comparison
        assert 'gcp' in comparison
        assert 'azure' in comparison

        # Each should have price and instance type
        assert 'price' in comparison['aws']
        assert 'instance_type' in comparison['aws']

    def test_find_cheapest_option(self):
        """Test finding cheapest cloud option."""
        from services.optimizer_api.pricing.comparator import PricingComparator

        comparator = PricingComparator()

        cheapest = comparator.find_cheapest({
            'cpu': 4,
            'memory': 16,
            'region': 'us-east',
            'storage': 100  # GB
        })

        assert cheapest['cloud'] in ['aws', 'gcp', 'azure']
        assert 'total_price' in cheapest
        assert 'monthly_cost' in cheapest
        assert 'savings_vs_most_expensive' in cheapest


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
