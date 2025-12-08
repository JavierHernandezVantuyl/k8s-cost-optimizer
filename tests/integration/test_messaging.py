"""
Integration tests for Redis messaging and caching.

Tests pub/sub, caching, and job queues using Redis.
"""

import pytest
import asyncio
import redis.asyncio as redis
import json


@pytest.fixture
async def redis_client():
    """Create Redis client."""
    client = await redis.from_url('redis://localhost:6379', decode_responses=True)
    yield client
    await client.close()


class TestRedisPubSub:
    """Test Redis pub/sub messaging."""

    @pytest.mark.asyncio
    async def test_publish_subscribe_pattern(self, redis_client):
        """Test basic pub/sub pattern."""
        pubsub = redis_client.pubsub()
        await pubsub.subscribe('analysis:updates')

        # Publish message
        await redis_client.publish('analysis:updates', json.dumps({
            'analysis_id': 'test-123',
            'status': 'completed',
            'workloads_analyzed': 50
        }))

        # Receive message
        message = await pubsub.get_message(timeout=5.0)
        while message and message['type'] != 'message':
            message = await pubsub.get_message(timeout=5.0)

        assert message is not None
        data = json.loads(message['data'])
        assert data['analysis_id'] == 'test-123'

        await pubsub.unsubscribe('analysis:updates')

    @pytest.mark.asyncio
    async def test_pattern_subscription(self, redis_client):
        """Test pattern-based subscription."""
        pubsub = redis_client.pubsub()
        await pubsub.psubscribe('cluster:*:events')

        # Publish to different cluster channels
        await redis_client.publish('cluster:aws-prod:events', json.dumps({
            'event': 'node_added'
        }))

        await redis_client.publish('cluster:gcp-staging:events', json.dumps({
            'event': 'pod_scaled'
        }))

        # Should receive both
        messages = []
        for _ in range(2):
            msg = await pubsub.get_message(timeout=5.0)
            while msg and msg['type'] != 'pmessage':
                msg = await pubsub.get_message(timeout=5.0)
            if msg:
                messages.append(msg)

        assert len(messages) == 2
        await pubsub.punsubscribe('cluster:*:events')


class TestRedisCaching:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_set_and_get_cache(self, redis_client):
        """Test basic cache operations."""
        # Set cache
        await redis_client.setex(
            'pricing:aws:t3.medium:us-east-1',
            3600,  # 1 hour TTL
            json.dumps({'price': 0.0416})
        )

        # Get cache
        cached = await redis_client.get('pricing:aws:t3.medium:us-east-1')
        data = json.loads(cached)

        assert data['price'] == 0.0416

    @pytest.mark.asyncio
    async def test_cache_expiration(self, redis_client):
        """Test cache TTL expiration."""
        # Set with 1 second TTL
        await redis_client.setex('temp:key', 1, 'value')

        # Should exist immediately
        assert await redis_client.exists('temp:key') == 1

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert await redis_client.exists('temp:key') == 0

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, redis_client):
        """Test manual cache invalidation."""
        # Set multiple cache keys
        await redis_client.set('cache:workload:api-1', 'data1')
        await redis_client.set('cache:workload:api-2', 'data2')
        await redis_client.set('cache:workload:worker-1', 'data3')

        # Invalidate workload caches
        keys = await redis_client.keys('cache:workload:*')
        if keys:
            await redis_client.delete(*keys)

        # Should be empty
        remaining = await redis_client.keys('cache:workload:*')
        assert len(remaining) == 0


class TestRedisJobQueue:
    """Test Redis-based job queue."""

    @pytest.mark.asyncio
    async def test_enqueue_job(self, redis_client):
        """Test adding job to queue."""
        job = {
            'id': 'job-123',
            'type': 'analyze_workload',
            'payload': {
                'workload': 'api-service',
                'namespace': 'production'
            }
        }

        # Add to queue
        await redis_client.lpush('jobs:analysis', json.dumps(job))

        # Verify queue length
        length = await redis_client.llen('jobs:analysis')
        assert length >= 1

    @pytest.mark.asyncio
    async def test_dequeue_and_process_job(self, redis_client):
        """Test dequeuing and processing jobs."""
        # Add job
        job = {'id': 'job-456', 'type': 'optimize'}
        await redis_client.lpush('jobs:optimization', json.dumps(job))

        # Dequeue (blocking pop with timeout)
        result = await redis_client.brpop('jobs:optimization', timeout=1)

        assert result is not None
        queue_name, job_data = result
        job_obj = json.loads(job_data)
        assert job_obj['id'] == 'job-456'

    @pytest.mark.asyncio
    async def test_job_priority_queue(self, redis_client):
        """Test priority-based job processing."""
        # Add jobs with different priorities
        await redis_client.zadd('jobs:priority', {
            json.dumps({'id': 'low', 'priority': 1}): 1,
            json.dumps({'id': 'high', 'priority': 10}): 10,
            json.dumps({'id': 'medium', 'priority': 5}): 5
        })

        # Pop highest priority
        result = await redis_client.zpopmax('jobs:priority', 1)

        assert len(result) > 0
        job_data, score = result[0]
        job = json.loads(job_data)
        assert job['id'] == 'high'  # Highest priority


class TestRedisRateLimiting:
    """Test rate limiting using Redis."""

    @pytest.mark.asyncio
    async def test_token_bucket_rate_limit(self, redis_client):
        """Test token bucket algorithm for rate limiting."""
        key = 'ratelimit:api:user-123'
        limit = 10  # 10 requests
        window = 60  # per minute

        async def check_rate_limit():
            # Increment counter
            count = await redis_client.incr(key)

            if count == 1:
                # Set expiration on first request
                await redis_client.expire(key, window)

            return count <= limit

        # Make requests
        results = []
        for _ in range(15):  # Try 15 requests
            allowed = await check_rate_limit()
            results.append(allowed)

        # First 10 should be allowed
        assert sum(results[:10]) == 10
        # Last 5 should be denied
        assert sum(results[10:]) == 0


class TestRedisDistributedLock:
    """Test distributed locking with Redis."""

    @pytest.mark.asyncio
    async def test_acquire_and_release_lock(self, redis_client):
        """Test acquiring and releasing distributed lock."""
        lock_key = 'lock:analysis:cluster-1'

        # Acquire lock
        acquired = await redis_client.set(
            lock_key,
            'worker-1',
            nx=True,  # Only set if not exists
            ex=30  # 30 second expiration
        )

        assert acquired is True

        # Try to acquire again (should fail)
        acquired_again = await redis_client.set(
            lock_key,
            'worker-2',
            nx=True,
            ex=30
        )

        assert acquired_again is False

        # Release lock
        await redis_client.delete(lock_key)

        # Now can acquire
        acquired_after_release = await redis_client.set(
            lock_key,
            'worker-2',
            nx=True,
            ex=30
        )

        assert acquired_after_release is True


class TestRedisStreams:
    """Test Redis Streams for event logging."""

    @pytest.mark.asyncio
    async def test_add_to_stream(self, redis_client):
        """Test adding events to Redis stream."""
        stream_key = 'events:optimizations'

        # Add event
        event_id = await redis_client.xadd(
            stream_key,
            {
                'type': 'recommendation_applied',
                'workload': 'api-service',
                'timestamp': str(asyncio.get_event_loop().time())
            }
        )

        assert event_id is not None

    @pytest.mark.asyncio
    async def test_read_from_stream(self, redis_client):
        """Test reading events from stream."""
        stream_key = 'events:analysis'

        # Add events
        for i in range(5):
            await redis_client.xadd(stream_key, {
                'event': f'workload_analyzed_{i}'
            })

        # Read events
        events = await redis_client.xread(
            {stream_key: '0'},  # Read from beginning
            count=10
        )

        assert len(events) > 0
        assert len(events[0][1]) >= 5  # At least 5 events

    @pytest.mark.asyncio
    async def test_consumer_group_processing(self, redis_client):
        """Test consumer groups for parallel processing."""
        stream_key = 'jobs:stream'
        group = 'processors'

        # Create consumer group
        try:
            await redis_client.xgroup_create(stream_key, group, '0', mkstream=True)
        except Exception:
            pass  # Group may already exist

        # Add jobs
        for i in range(3):
            await redis_client.xadd(stream_key, {'job_id': f'job-{i}'})

        # Read as consumer
        messages = await redis_client.xreadgroup(
            group,
            'consumer-1',
            {stream_key: '>'},
            count=2
        )

        assert len(messages) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
