"""
Shared pytest fixtures and utilities for all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
import os
import tempfile


# ==============================================================================
# Session-scoped fixtures (created once per test session)
# ==============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    return {
        'api_url': os.getenv('API_URL', 'http://localhost:8000'),
        'dashboard_url': os.getenv('DASHBOARD_URL', 'http://localhost:3000'),
        'postgres_url': os.getenv('POSTGRES_URL', 'postgresql://test:test@localhost:5432/k8s_optimizer_test'),
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'kubeconfig': os.getenv('KUBECONFIG', '~/.kube/config'),
    }


# ==============================================================================
# Function-scoped fixtures (created for each test function)
# ==============================================================================

@pytest.fixture
def sample_workload() -> Dict[str, Any]:
    """Sample Kubernetes workload for testing."""
    return {
        'name': 'test-app',
        'namespace': 'default',
        'type': 'Deployment',
        'replicas': 3,
        'containers': [{
            'name': 'main',
            'image': 'nginx:latest',
            'requests': {
                'cpu': '500m',
                'memory': '512Mi'
            },
            'limits': {
                'cpu': '1000m',
                'memory': '1Gi'
            }
        }]
    }


@pytest.fixture
def sample_metrics() -> Dict[str, Any]:
    """Sample metrics data."""
    return {
        'cpu': {
            'avg': 250,  # millicores
            'p95': 350,
            'p99': 450,
            'max': 800
        },
        'memory': {
            'avg': 256,  # MiB
            'p95': 384,
            'p99': 450,
            'max': 600
        },
        'network': {
            'in_bytes': 1000000,
            'out_bytes': 500000
        }
    }


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_pricing_data() -> Dict[str, Any]:
    """Mock cloud pricing data."""
    return {
        'aws': {
            't3.micro': {'cpu': 2, 'memory': 1, 'price_hourly': 0.0104},
            't3.small': {'cpu': 2, 'memory': 2, 'price_hourly': 0.0208},
            't3.medium': {'cpu': 2, 'memory': 4, 'price_hourly': 0.0416},
            't3.large': {'cpu': 2, 'memory': 8, 'price_hourly': 0.0832},
        },
        'gcp': {
            'n1-standard-1': {'cpu': 1, 'memory': 3.75, 'price_hourly': 0.0475},
            'n1-standard-2': {'cpu': 2, 'memory': 7.5, 'price_hourly': 0.0950},
            'n1-standard-4': {'cpu': 4, 'memory': 15, 'price_hourly': 0.1900},
        },
        'azure': {
            'Standard_B1s': {'cpu': 1, 'memory': 1, 'price_hourly': 0.0104},
            'Standard_B2s': {'cpu': 2, 'memory': 4, 'price_hourly': 0.0416},
            'Standard_D2s_v3': {'cpu': 2, 'memory': 8, 'price_hourly': 0.096},
        }
    }


# ==============================================================================
# Database fixtures
# ==============================================================================

@pytest.fixture
async def db_connection(test_config):
    """Create database connection for tests."""
    import asyncpg

    conn = await asyncpg.connect(test_config['postgres_url'])
    yield conn
    await conn.close()


@pytest.fixture
async def clean_database(db_connection):
    """Clean database before and after tests."""
    # Clean before test
    await db_connection.execute('TRUNCATE TABLE recommendations CASCADE')
    await db_connection.execute('TRUNCATE TABLE analyses CASCADE')
    await db_connection.execute('TRUNCATE TABLE daily_costs CASCADE')

    yield

    # Clean after test
    await db_connection.execute('TRUNCATE TABLE recommendations CASCADE')
    await db_connection.execute('TRUNCATE TABLE analyses CASCADE')
    await db_connection.execute('TRUNCATE TABLE daily_costs CASCADE')


# ==============================================================================
# Redis fixtures
# ==============================================================================

@pytest.fixture
async def redis_client(test_config):
    """Create Redis client for tests."""
    import redis.asyncio as redis

    client = await redis.from_url(test_config['redis_url'])
    yield client
    await client.flushdb()  # Clean up
    await client.close()


# ==============================================================================
# API fixtures
# ==============================================================================

@pytest.fixture
async def api_client(test_config):
    """Create HTTP client for API tests."""
    import httpx

    async with httpx.AsyncClient(base_url=test_config['api_url']) as client:
        yield client


# ==============================================================================
# Kubernetes fixtures
# ==============================================================================

@pytest.fixture
def k8s_client():
    """Create Kubernetes client."""
    from kubernetes import client, config

    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture
def k8s_apps_client():
    """Create Kubernetes Apps API client."""
    from kubernetes import client, config

    config.load_kube_config()
    return client.AppsV1Api()


# ==============================================================================
# Helper functions
# ==============================================================================

def parse_resource(resource_str: str, resource_type: str = 'cpu') -> float:
    """Parse Kubernetes resource string to numeric value."""
    if resource_type == 'cpu':
        if resource_str.endswith('m'):
            return int(resource_str[:-1])
        return float(resource_str) * 1000  # Convert cores to millicores
    elif resource_type == 'memory':
        if resource_str.endswith('Gi'):
            return float(resource_str[:-2]) * 1024  # Convert to MiB
        elif resource_str.endswith('Mi'):
            return float(resource_str[:-2])
        elif resource_str.endswith('Ki'):
            return float(resource_str[:-2]) / 1024  # Convert to MiB
    return float(resource_str)


@pytest.fixture
def resource_parser():
    """Provide resource parsing helper."""
    return parse_resource


# ==============================================================================
# Markers and skip conditions
# ==============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, no dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Skip integration tests if services not available
def pytest_collection_modifyitems(config, items):
    """Modify test collection based on available services."""
    import socket

    def check_service(host, port):
        """Check if service is available."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    # Check for services
    postgres_available = check_service('localhost', 5432)
    redis_available = check_service('localhost', 6379)
    api_available = check_service('localhost', 8000)

    skip_postgres = pytest.mark.skip(reason="PostgreSQL not available")
    skip_redis = pytest.mark.skip(reason="Redis not available")
    skip_integration = pytest.mark.skip(reason="Integration services not available")

    for item in items:
        if "postgres" in item.keywords and not postgres_available:
            item.add_marker(skip_postgres)
        if "redis" in item.keywords and not redis_available:
            item.add_marker(skip_redis)
        if "integration" in item.keywords and not (postgres_available and redis_available and api_available):
            item.add_marker(skip_integration)
