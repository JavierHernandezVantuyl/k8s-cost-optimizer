# Testing Troubleshooting Guide

Quick reference for resolving common testing issues.

## Quick Diagnostics

```bash
# Check service health
./scripts/health-check.sh

# Verify all dependencies installed
pip list | grep -E "pytest|locust|cypress"

# Check database connection
psql postgresql://test:test@localhost:5432/k8s_optimizer_test -c "SELECT 1"

# Check Redis connection
redis-cli ping

# Check API health
curl http://localhost:8000/health
```

## Common Errors

### 1. ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'services'
```

**Solutions:**
```bash
# Option 1: Install in editable mode
pip install -e .

# Option 2: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Option 3: Add to pytest.ini
# testpaths = .
```

### 2. Database Connection Errors

**Error:**
```
asyncpg.exceptions.InvalidCatalogNameError: database "k8s_optimizer_test" does not exist
```

**Solution:**
```bash
# Create test database
createdb k8s_optimizer_test

# Or use docker-compose
docker-compose up -d postgres

# Run migrations
alembic upgrade head
```

### 3. Redis Connection Errors

**Error:**
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379. Connection refused
```

**Solution:**
```bash
# Start Redis
docker-compose up -d redis

# Or install locally (macOS)
brew install redis
brew services start redis

# Verify
redis-cli ping  # Should return "PONG"
```

### 4. Kubernetes Test Failures

**Error:**
```
kubernetes.config.config_exception.ConfigException: Invalid kube-config file
```

**Solution:**
```bash
# Check kubeconfig exists
ls -la ~/.kube/config

# Set environment variable
export KUBECONFIG=~/.kube/config

# Use test context
kubectl config use-context docker-desktop

# Skip k8s tests if not needed
pytest -m "not kubernetes"
```

### 5. Load Test Port Conflicts

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8089 (Locust default)
lsof -ti:8089

# Kill the process
kill $(lsof -ti:8089)

# Or use different port
locust -f locustfile.py --web-port 8090
```

### 6. E2E Test Failures

**Error:**
```
CypressError: Timed out retrying: Expected to find element: '[data-testid="total-savings"]'
```

**Solutions:**
```bash
# 1. Ensure dashboard is running
npm run dev

# 2. Check correct URL in cypress.config.js
# baseUrl: 'http://localhost:3000'

# 3. Increase timeout
# defaultCommandTimeout: 10000

# 4. Run in headed mode to debug
npx cypress open
```

### 7. Fixture Not Found

**Error:**
```
pytest.fixtures.FixtureLookupError: fixture 'test_cluster_config' not found
```

**Solution:**
```bash
# Ensure conftest.py is in correct location
ls tests/conftest.py

# Check fixture is defined
grep "def test_cluster_config" tests/conftest.py

# Run with verbose fixture info
pytest --fixtures
```

### 8. Coverage Report Errors

**Error:**
```
CoverageWarning: No data was collected
```

**Solution:**
```bash
# Ensure source path is correct
pytest --cov=services --cov-report=html

# Check .coveragerc or pytest.ini
# [coverage:run]
# source = services

# Run with debug
pytest --cov-report=term-missing -vv
```

### 9. Async Test Errors

**Error:**
```
RuntimeError: This event loop is already running
```

**Solution:**
```python
# Use pytest-asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_call()
    assert result is not None

# Or configure in pytest.ini
# asyncio_mode = auto
```

### 10. Import Circular Dependencies

**Error:**
```
ImportError: cannot import name 'X' from partially initialized module
```

**Solution:**
```python
# Move imports inside functions
def my_function():
    from services.optimizer import Optimizer
    return Optimizer()

# Or restructure code to avoid circular imports
# Move shared code to separate module
```

## Performance Issues

### Slow Tests

**Problem:** Tests take too long to run

**Solutions:**
```bash
# 1. Run tests in parallel
pytest -n auto

# 2. Skip slow tests during development
pytest -m "not slow"

# 3. Use faster fixtures
# Change from function scope to session scope

# 4. Profile tests
pytest --durations=10
```

### High Memory Usage

**Problem:** Tests consuming too much memory

**Solutions:**
```bash
# 1. Run fewer tests at once
pytest tests/unit -k "test_optimizer"

# 2. Clear fixtures after each test
@pytest.fixture
def my_fixture():
    data = create_large_dataset()
    yield data
    del data  # Explicit cleanup

# 3. Use generators for large datasets
@pytest.fixture
def large_dataset():
    for item in generate_items():
        yield item
```

## CI/CD Specific Issues

### Tests Pass Locally, Fail in CI

**Common Causes:**

1. **Timing issues**
```python
# Add retries for flaky tests
@pytest.mark.flaky(reruns=3)
def test_api_call():
    pass
```

2. **Environment differences**
```yaml
# Ensure CI environment matches local
env:
  PYTHONPATH: .
  DATABASE_URL: postgresql://...
```

3. **Resource constraints**
```yaml
# Reduce parallel jobs
jobs:
  test:
    strategy:
      max-parallel: 2  # Instead of 4
```

### Timeout Errors in CI

**Solution:**
```yaml
# Increase timeout in GitHub Actions
- name: Run tests
  run: pytest --timeout=600
  timeout-minutes: 15
```

## Docker-Specific Issues

### Container Won't Start

```bash
# Check logs
docker-compose logs postgres

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check resource limits
docker stats
```

### Volume Permission Issues

```bash
# Fix permissions
sudo chown -R $(whoami) ./data

# Or use named volumes
# In docker-compose.yml:
# volumes:
#   - postgres_data:/var/lib/postgresql/data
```

## Load Testing Issues

### Locust Can't Connect to Target

```bash
# Check API is running
curl http://localhost:8000/health

# Use correct host parameter
locust -f locustfile.py --host=http://localhost:8000

# Check firewall rules
# Ensure port 8000 is accessible
```

### High Error Rate During Load Test

**Investigation:**
```bash
# 1. Check API logs
docker-compose logs api

# 2. Monitor resource usage
htop  # Or: docker stats

# 3. Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity"

# 4. Reduce spawn rate
locust -f locustfile.py --spawn-rate 10  # Instead of 100
```

## Getting Detailed Debug Info

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in pytest
pytest -v -s --log-cli-level=DEBUG
```

### Capture Request/Response

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(url)
    print(f"Request: {client.last_request}")
    print(f"Response: {response.text}")
```

### Database Query Logging

```python
# Enable SQL echo
engine = create_async_engine(
    database_url,
    echo=True  # Logs all SQL queries
)
```

## Still Having Issues?

1. **Check test logs:** `pytest -vv -s > test_output.log 2>&1`
2. **Search existing issues:** Check GitHub issues
3. **Minimal reproduction:** Create minimal test case
4. **Environment details:** Python version, OS, dependency versions
5. **Open issue:** Include test output, environment, and steps to reproduce

### Useful Commands for Bug Reports

```bash
# Collect environment info
python --version
pip freeze > requirements-frozen.txt
pytest --version
docker --version

# Run single failing test with maximum verbosity
pytest tests/path/to/test.py::test_name -vv -s --tb=long

# Capture full output
pytest -vv -s --tb=long > full_output.log 2>&1
```
