# Testing Guide - K8s Cost Optimizer

Comprehensive testing documentation covering unit, integration, E2E, load, and chaos tests.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Types](#test-types)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Load Testing](#load-testing)
6. [E2E Testing](#e2e-testing)
7. [Chaos Engineering](#chaos-engineering)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt
npm install  # For E2E tests

# Run all unit tests
pytest tests/unit -v

# Run specific test file
pytest tests/unit/test_optimizer.py -v

# Run with coverage
pytest --cov=services --cov-report=html

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Run E2E tests
cd tests/e2e && npx cypress run
```

## Test Types

### Unit Tests (tests/unit/)

**Purpose:** Test individual components in isolation
**Speed:** Fast (<1s per test)
**Dependencies:** None (mocked)
**Coverage Target:** 80%+

**Test Files:**
- `test_pricing_apis.py` - Cloud pricing API integrations
- `test_optimizer.py` - Optimization algorithms
- `test_cost_calculator.py` - Cost calculation logic
- `test_recommendations.py` - Recommendation generation

**Running:**
```bash
pytest tests/unit -v -m unit
```

### Integration Tests (tests/integration/)

**Purpose:** Test interaction between components
**Speed:** Medium (1-10s per test)
**Dependencies:** PostgreSQL, Redis, Kubernetes
**Coverage Target:** 60%+

**Test Files:**
- `test_full_flow.py` - Complete optimization workflow
- `test_api_integration.py` - REST API endpoints
- `test_database.py` - Database operations
- `test_messaging.py` - Redis pub/sub and caching

**Running:**
```bash
# Start dependencies first
docker-compose up -d postgres redis

# Run integration tests
pytest tests/integration -v -m integration
```

### E2E Tests (tests/e2e/)

**Purpose:** Test complete user workflows
**Tool:** Cypress
**Speed:** Slow (30s-2min per test)
**Dependencies:** Full application stack

**Test Scenarios:**
- Dashboard navigation
- Viewing recommendations
- Applying optimizations
- Cost tracking
- Multi-device responsiveness

**Running:**
```bash
# Interactive mode (development)
cd tests/e2e && npx cypress open

# Headless mode (CI)
cd tests/e2e && npx cypress run
```

### Load Tests (tests/load/)

**Purpose:** Test system under high load
**Tool:** Locust
**Target:** 1000 concurrent users
**Metrics:** Response time, throughput, error rate

**Scenarios:**
- Normal load (gradual ramp-up)
- Spike test (sudden traffic bursts)
- Stress test (find breaking point)

**Running:**
```bash
# Start load test with UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode for CI
locust -f tests/load/locustfile.py \
    --headless \
    --users 1000 \
    --spawn-rate 100 \
    --run-time 10m \
    --host=http://localhost:8000
```

### Chaos Tests (tests/chaos/)

**Purpose:** Test resilience to failures
**Risk:** Destructive (use test environments only)

**Scenarios:**
- Pod failures
- Network partitions
- Resource exhaustion
- Dependency failures

**Running:**
```bash
# WARNING: Only run in test environments!
pytest tests/chaos -v -m chaos
```

## Test Coverage

### Current Coverage

```
Name                                  Stmts   Miss  Cover
---------------------------------------------------------
services/optimizer_api/pricing.py      245     23    91%
services/optimizer_api/optimizer.py    420     52    88%
services/optimizer_api/calculator.py   180     18    90%
services/optimizer_api/recommender.py  310     38    88%
---------------------------------------------------------
TOTAL                                 1560    154    90%
```

### Viewing Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=services --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage Goals

- **Overall:** 80%+
- **Critical paths:** 90%+
- **New code:** 85%+

## Load Testing

### Performance Thresholds

| Metric | Threshold | Current |
|--------|-----------|---------|
| Median Response Time | <500ms | 245ms |
| 95th Percentile | <2000ms | 680ms |
| Error Rate | <1% | 0.12% |
| Throughput | >100 req/s | 156 req/s |

### Load Test Scenarios

#### 1. Normal Load
```bash
locust -f tests/load/locustfile.py \
    --users 100 \
    --spawn-rate 10 \
    --run-time 10m
```

#### 2. Spike Test
```bash
locust -f tests/load/scenarios/spike_test.py \
    --users 1000 \
    --spawn-rate 100
```

#### 3. Stress Test
```bash
locust -f tests/load/scenarios/stress_test.py \
    --users 2000 \
    --spawn-rate 50
```

### Analyzing Results

Load test results are saved to `tests/load/reports/`.

Key metrics to monitor:
- Response time distribution
- Error rate by endpoint
- Throughput over time
- Resource utilization (CPU, memory)

## E2E Testing

### Test Organization

```
tests/e2e/
├── cypress/
│   ├── integration/
│   │   └── dashboard.spec.js    # Main UI tests
│   ├── fixtures/                # Test data
│   ├── support/                 # Helper functions
│   └── screenshots/             # Failure screenshots
└── cypress.config.js
```

### Writing E2E Tests

```javascript
describe('Recommendations Page', () => {
  beforeEach(() => {
    cy.visit('/recommendations')
  })

  it('should display recommendations', () => {
    cy.get('[data-testid="recommendation-card"]')
      .should('have.length.at.least', 1)
  })
})
```

### Best Practices

1. Use `data-testid` attributes for selectors
2. Avoid brittle selectors (class names, DOM structure)
3. Use fixtures for test data
4. Take screenshots on failure
5. Test on multiple viewports

## Chaos Engineering

### Safety Guidelines

⚠️ **IMPORTANT:** Only run chaos tests in isolated test environments!

- Never run against production
- Use separate test clusters
- Have rollback plans ready
- Monitor during chaos tests

### Chaos Scenarios

```bash
# Test pod failure recovery
pytest tests/chaos/test_resilience.py::TestPodResilience -v

# Test network partitions
pytest tests/chaos/test_resilience.py::TestNetworkChaos -v

# Test resource exhaustion
pytest tests/chaos/test_resilience.py::TestResourceExhaustion -v
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Nightly schedule

### Test Workflow

```yaml
# .github/workflows/tests.yml
- name: Run unit tests
  run: pytest tests/unit -v --cov

- name: Run integration tests
  run: pytest tests/integration -v

- name: Run E2E tests
  run: cd tests/e2e && npx cypress run
```

### Quality Gates

Pull requests must pass:
- ✅ All unit tests
- ✅ All integration tests
- ✅ Coverage >= 80%
- ✅ No critical vulnerabilities
- ✅ Load test thresholds

## Troubleshooting

### Common Issues

#### 1. "Connection refused" errors

**Cause:** Required services not running

**Solution:**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs postgres redis
```

#### 2. Tests timing out

**Cause:** Slow database or network

**Solution:**
```bash
# Increase pytest timeout
pytest --timeout=600

# Or skip slow tests
pytest -m "not slow"
```

#### 3. Import errors

**Cause:** Missing dependencies or PYTHONPATH

**Solution:**
```bash
# Install all dependencies
pip install -r requirements-test.txt

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 4. Kubernetes tests failing

**Cause:** No kubeconfig or wrong context

**Solution:**
```bash
# Set kubeconfig
export KUBECONFIG=~/.kube/config

# Use test cluster context
kubectl config use-context test-cluster

# Or skip k8s tests
pytest -m "not kubernetes"
```

#### 5. E2E tests failing

**Cause:** Dashboard not running or wrong URL

**Solution:**
```bash
# Start dashboard
npm run dev

# Set correct URL in cypress.config.js
baseUrl: 'http://localhost:3000'
```

### Debug Mode

```bash
# Run with verbose output
pytest -vv -s

# Run single test with debugging
pytest tests/unit/test_optimizer.py::test_specific -vv -s --pdb

# Enable SQL query logging
export SQL_ECHO=true

# Enable debug logging
export LOG_LEVEL=DEBUG
```

### Getting Help

1. Check this documentation
2. View test examples in each test file
3. Check CI/CD logs for similar errors
4. Ask in #testing Slack channel
5. Open issue with test output and environment details

## Best Practices

### Writing Tests

1. **Descriptive names:** `test_right_sizing_reduces_cpu_request`
2. **One assertion per test:** Test one thing
3. **Use fixtures:** Share setup code
4. **Mock external services:** Keep tests fast
5. **Test edge cases:** Not just happy path

### Test Organization

```python
class TestOptimizer:
    """Test the optimizer module."""

    def test_normal_case(self):
        """Test typical optimization scenario."""
        pass

    def test_edge_case(self):
        """Test edge case with minimal data."""
        pass

    def test_error_handling(self):
        """Test error conditions."""
        pass
```

### Performance

- Keep unit tests fast (<1s)
- Use `pytest-xdist` for parallel execution
- Mark slow tests with `@pytest.mark.slow`
- Cache expensive fixtures at session scope

### Maintenance

- Update tests when changing features
- Remove obsolete tests
- Keep test data realistic
- Document complex test scenarios
- Review test coverage regularly

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Cypress Documentation](https://docs.cypress.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
