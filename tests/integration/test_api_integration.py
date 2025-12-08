"""
Integration tests for API endpoints.

Tests all REST API endpoints with real database and services.
"""

import pytest
import httpx
from datetime import datetime, timedelta


@pytest.fixture
async def api_client():
    """Create test API client."""
    async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
        yield client


class TestAnalysisAPI:
    """Test analysis API endpoints."""

    @pytest.mark.asyncio
    async def test_start_analysis(self, api_client):
        """Test POST /api/v1/analysis endpoint."""
        response = await api_client.post('/api/v1/analysis', json={
            'cluster_id': 'test-cluster',
            'namespaces': ['production'],
            'lookback_days': 7
        })

        assert response.status_code == 202
        data = response.json()
        assert 'analysis_id' in data
        assert data['status'] == 'started'

    @pytest.mark.asyncio
    async def test_get_analysis_status(self, api_client):
        """Test GET /api/v1/analysis/{id}/status endpoint."""
        # Start analysis first
        start_response = await api_client.post('/api/v1/analysis', json={
            'cluster_id': 'test-cluster',
            'namespaces': ['production']
        })
        analysis_id = start_response.json()['analysis_id']

        # Get status
        response = await api_client.get(f'/api/v1/analysis/{analysis_id}/status')

        assert response.status_code == 200
        data = response.json()
        assert data['analysis_id'] == analysis_id
        assert data['status'] in ['pending', 'running', 'completed', 'failed']


class TestRecommendationsAPI:
    """Test recommendations API endpoints."""

    @pytest.mark.asyncio
    async def test_get_recommendations(self, api_client):
        """Test GET /api/v1/recommendations endpoint."""
        response = await api_client.get('/api/v1/recommendations', params={
            'namespace': 'production',
            'min_confidence': 0.7
        })

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['recommendations'], list)
        assert all(r['confidence'] >= 0.7 for r in data['recommendations'])

    @pytest.mark.asyncio
    async def test_get_recommendation_details(self, api_client):
        """Test GET /api/v1/recommendations/{id} endpoint."""
        # First get list
        list_response = await api_client.get('/api/v1/recommendations')
        recommendations = list_response.json()['recommendations']

        if len(recommendations) > 0:
            rec_id = recommendations[0]['id']

            # Get details
            response = await api_client.get(f'/api/v1/recommendations/{rec_id}')

            assert response.status_code == 200
            data = response.json()
            assert data['id'] == rec_id
            assert 'type' in data
            assert 'workload' in data
            assert 'savings' in data

    @pytest.mark.asyncio
    async def test_apply_recommendation(self, api_client):
        """Test POST /api/v1/recommendations/{id}/apply endpoint."""
        # Get a recommendation
        list_response = await api_client.get('/api/v1/recommendations')
        recommendations = list_response.json()['recommendations']

        if len(recommendations) > 0:
            rec_id = recommendations[0]['id']

            # Apply in dry-run mode
            response = await api_client.post(
                f'/api/v1/recommendations/{rec_id}/apply',
                json={'dry_run': True}
            )

            assert response.status_code in [200, 202]
            data = response.json()
            assert data['status'] in ['success', 'pending']


class TestClustersAPI:
    """Test cluster management API endpoints."""

    @pytest.mark.asyncio
    async def test_register_cluster(self, api_client):
        """Test POST /api/v1/clusters endpoint."""
        response = await api_client.post('/api/v1/clusters', json={
            'name': 'test-cluster',
            'cloud_provider': 'aws',
            'region': 'us-east-1',
            'kubeconfig': 'base64-encoded-kubeconfig'
        })

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'test-cluster'
        assert 'cluster_id' in data

    @pytest.mark.asyncio
    async def test_list_clusters(self, api_client):
        """Test GET /api/v1/clusters endpoint."""
        response = await api_client.get('/api/v1/clusters')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['clusters'], list)

    @pytest.mark.asyncio
    async def test_get_cluster_details(self, api_client):
        """Test GET /api/v1/clusters/{id} endpoint."""
        # List clusters first
        list_response = await api_client.get('/api/v1/clusters')
        clusters = list_response.json()['clusters']

        if len(clusters) > 0:
            cluster_id = clusters[0]['cluster_id']

            response = await api_client.get(f'/api/v1/clusters/{cluster_id}')

            assert response.status_code == 200
            data = response.json()
            assert data['cluster_id'] == cluster_id


class TestCostsAPI:
    """Test cost tracking API endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_costs(self, api_client):
        """Test GET /api/v1/costs/current endpoint."""
        response = await api_client.get('/api/v1/costs/current', params={
            'cluster_id': 'test-cluster'
        })

        assert response.status_code == 200
        data = response.json()
        assert 'total_cost' in data
        assert 'breakdown' in data

    @pytest.mark.asyncio
    async def test_get_cost_history(self, api_client):
        """Test GET /api/v1/costs/history endpoint."""
        response = await api_client.get('/api/v1/costs/history', params={
            'cluster_id': 'test-cluster',
            'days': 30
        })

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['daily_costs'], list)

    @pytest.mark.asyncio
    async def test_get_cost_forecast(self, api_client):
        """Test GET /api/v1/costs/forecast endpoint."""
        response = await api_client.get('/api/v1/costs/forecast', params={
            'cluster_id': 'test-cluster',
            'days': 30
        })

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data['forecast'], list)
        assert len(data['forecast']) == 30


class TestWebSocketAPI:
    """Test WebSocket endpoints for real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_analysis_updates(self):
        """Test WebSocket for real-time analysis updates."""
        import websockets

        async with websockets.connect('ws://localhost:8000/ws/analysis/test-id') as ws:
            # Send subscribe message
            await ws.send('{"action": "subscribe"}')

            # Receive updates
            update = await ws.recv()
            data = eval(update)  # In real test, use json.loads

            assert 'status' in data
            assert 'progress' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
