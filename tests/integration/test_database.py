"""
Integration tests for database operations.

Tests PostgreSQL database interactions, transactions, and migrations.
"""

import pytest
from datetime import datetime, timedelta
import asyncpg


@pytest.fixture
async def db_pool():
    """Create database connection pool."""
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='k8s_optimizer_test',
        user='test',
        password='test',
        min_size=2,
        max_size=10
    )
    yield pool
    await pool.close()


class TestRecommendationsTable:
    """Test recommendations table operations."""

    @pytest.mark.asyncio
    async def test_insert_recommendation(self, db_pool):
        """Test inserting recommendation."""
        async with db_pool.acquire() as conn:
            rec_id = await conn.fetchval("""
                INSERT INTO recommendations (
                    analysis_id, type, workload_name, namespace,
                    confidence, monthly_savings, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, 'test-analysis', 'right_sizing', 'api-service', 'production',
                0.85, 500.0, 'pending')

            assert rec_id is not None

    @pytest.mark.asyncio
    async def test_query_recommendations_by_confidence(self, db_pool):
        """Test querying recommendations with confidence filter."""
        async with db_pool.acquire() as conn:
            recommendations = await conn.fetch("""
                SELECT * FROM recommendations
                WHERE confidence >= $1 AND status = $2
                ORDER BY monthly_savings DESC
            """, 0.8, 'pending')

            assert all(r['confidence'] >= 0.8 for r in recommendations)

    @pytest.mark.asyncio
    async def test_update_recommendation_status(self, db_pool):
        """Test updating recommendation status."""
        async with db_pool.acquire() as conn:
            # Insert test record
            rec_id = await conn.fetchval("""
                INSERT INTO recommendations (
                    analysis_id, type, workload_name, namespace, status
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, 'test', 'right_sizing', 'test-app', 'default', 'pending')

            # Update status
            await conn.execute("""
                UPDATE recommendations
                SET status = $1, applied_at = $2
                WHERE id = $3
            """, 'applied', datetime.now(), rec_id)

            # Verify
            status = await conn.fetchval("""
                SELECT status FROM recommendations WHERE id = $1
            """, rec_id)

            assert status == 'applied'


class TestCostsTable:
    """Test costs table operations."""

    @pytest.mark.asyncio
    async def test_insert_daily_costs(self, db_pool):
        """Test inserting daily cost records."""
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO daily_costs (
                    cluster_id, date, compute_cost, storage_cost, network_cost
                ) VALUES ($1, $2, $3, $4, $5)
            """, 'test-cluster', datetime.now().date(), 1000.0, 200.0, 50.0)

    @pytest.mark.asyncio
    async def test_aggregate_monthly_costs(self, db_pool):
        """Test aggregating costs by month."""
        async with db_pool.acquire() as conn:
            # Insert 30 days of data
            for i in range(30):
                date = datetime.now().date() - timedelta(days=i)
                await conn.execute("""
                    INSERT INTO daily_costs (
                        cluster_id, date, compute_cost, storage_cost, network_cost
                    ) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (cluster_id, date) DO NOTHING
                """, 'test-cluster', date, 1000.0, 200.0, 50.0)

            # Aggregate
            monthly_total = await conn.fetchval("""
                SELECT SUM(compute_cost + storage_cost + network_cost)
                FROM daily_costs
                WHERE cluster_id = $1
                AND date >= CURRENT_DATE - INTERVAL '30 days'
            """, 'test-cluster')

            expected_total = (1000.0 + 200.0 + 50.0) * 30
            assert monthly_total == pytest.approx(expected_total, 0.01)


class TestAnalysisTable:
    """Test analysis table operations."""

    @pytest.mark.asyncio
    async def test_create_analysis_record(self, db_pool):
        """Test creating analysis record with transaction."""
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Create analysis
                analysis_id = await conn.fetchval("""
                    INSERT INTO analyses (
                        cluster_id, status, started_at
                    ) VALUES ($1, $2, $3)
                    RETURNING id
                """, 'test-cluster', 'running', datetime.now())

                # Create related workload records
                for i in range(10):
                    await conn.execute("""
                        INSERT INTO analyzed_workloads (
                            analysis_id, name, namespace
                        ) VALUES ($1, $2, $3)
                    """, analysis_id, f'workload-{i}', 'default')

                # Verify count
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM analyzed_workloads
                    WHERE analysis_id = $1
                """, analysis_id)

                assert count == 10


class TestOptimizationHistory:
    """Test optimization history tracking."""

    @pytest.mark.asyncio
    async def test_record_optimization_event(self, db_pool):
        """Test recording optimization application event."""
        async with db_pool.acquire() as conn:
            event_id = await conn.fetchval("""
                INSERT INTO optimization_events (
                    recommendation_id, event_type, timestamp, details
                ) VALUES ($1, $2, $3, $4)
                RETURNING id
            """, 'rec-123', 'applied', datetime.now(), '{"dry_run": false}')

            assert event_id is not None

    @pytest.mark.asyncio
    async def test_query_optimization_timeline(self, db_pool):
        """Test querying optimization timeline."""
        async with db_pool.acquire() as conn:
            timeline = await conn.fetch("""
                SELECT
                    e.timestamp,
                    e.event_type,
                    r.type as recommendation_type,
                    r.workload_name
                FROM optimization_events e
                JOIN recommendations r ON e.recommendation_id = r.id
                WHERE e.timestamp >= $1
                ORDER BY e.timestamp DESC
            """, datetime.now() - timedelta(days=7))

            assert isinstance(timeline, list)


class TestDatabasePerformance:
    """Test database performance and indexing."""

    @pytest.mark.asyncio
    async def test_query_performance_with_index(self, db_pool):
        """Test query performance with proper indexing."""
        import time

        async with db_pool.acquire() as conn:
            # Query using indexed column
            start = time.time()
            await conn.fetch("""
                SELECT * FROM recommendations
                WHERE created_at >= $1
                AND status = $2
            """, datetime.now() - timedelta(days=30), 'pending')

            elapsed = time.time() - start

            # Should be fast with index
            assert elapsed < 0.1  # Less than 100ms

    @pytest.mark.asyncio
    async def test_connection_pooling(self, db_pool):
        """Test connection pool efficiency."""
        # Execute multiple queries concurrently
        import asyncio

        async def query():
            async with db_pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM recommendations')

        # Run 20 concurrent queries
        results = await asyncio.gather(*[query() for _ in range(20)])

        assert len(results) == 20
        assert db_pool.get_size() <= 10  # Should reuse connections


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
