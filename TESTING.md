# Testing Guide

This document explains how to run the comprehensive test suite for the Kite Trading System.

## Test Types

### 1. Unit Tests

Test individual components and functions in isolation.

```bash
# Run all unit tests
pytest tests/test_*.py -m "not e2e"

# Run specific unit test modules
pytest tests/test_config.py -v
pytest tests/test_kite_client.py -v
pytest tests/test_ui_components.py -v
```

### 2. Integration Tests

Test the interaction between different components.

```bash
# Run integration tests
pytest tests/test_integration.py -v
```

### 3. End-to-End (E2E) Tests with Playwright

Test the complete user workflows through the browser.

#### Prerequisites for E2E Tests

1. Install Playwright browsers:

   ```bash
   python -m playwright install
   ```

2. Start the Streamlit app in test mode:
   ```bash
   # In one terminal
   streamlit run src/app.py --server.port=8502
   ```

#### Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific E2E test files
pytest tests/e2e/test_streamlit_app.py -v
pytest tests/e2e/test_order_management.py -v

# Run E2E tests with specific browser
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# Run E2E tests in headful mode (visible browser)
pytest tests/e2e/ --headed

# Run E2E tests with slow motion (for debugging)
pytest tests/e2e/ --slowmo 1000
```

#### E2E Test Configuration

The E2E tests automatically:

- Start a Streamlit app instance on port 8502
- Use test credentials (mock API responses)
- Clean up after tests complete
- Take screenshots on failure

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only E2E tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage

Generate test coverage reports:

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## Debugging Tests

### Debug Unit Tests

```bash
# Run with pdb debugger
pytest tests/test_kite_client.py::TestKiteClient::test_place_order_success --pdb

# Run with verbose output
pytest tests/ -v -s

# Run specific test with print statements
pytest tests/test_config.py -v -s
```

### Debug E2E Tests

```bash
# Run in headed mode to see browser
pytest tests/e2e/test_streamlit_app.py --headed

# Take screenshots on failure
pytest tests/e2e/ --screenshot=on

# Record video
pytest tests/e2e/ --video=on

# Debug specific test
pytest tests/e2e/test_streamlit_app.py::TestStreamlitApp::test_app_loads_successfully --headed --slowmo 2000
```

### Playwright Debug Tools

```bash
# Use Playwright inspector
pytest tests/e2e/ --headed --slowmo 1000 --pdb

# Generate test code
playwright codegen http://localhost:8502
```

## Test Data Management

### Mock Data

Tests use mock data to avoid dependency on actual Kite API:

```python
from tests.test_utils import TestDataFactory, MockKiteClientBuilder

# Create test orders
orders = [TestDataFactory.create_test_order(status="COMPLETE")]

# Build mock client
mock_client = (MockKiteClientBuilder()
    .with_orders(orders)
    .with_exception_on("get_margins", Exception("API Error"))
    .build())
```

### Environment Setup

Tests automatically handle environment configuration:

```python
from tests.test_utils import temporary_env_file

with temporary_env_file({"KITE_API_KEY": "test", "KITE_ACCESS_TOKEN": "test"}):
    # Test code here
    pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - run: pip install -r requirements.txt
      - run: python -m playwright install
      - run: pytest tests/ -v
      - run: pytest tests/e2e/ --browser chromium
```

## Performance Testing

### Load Testing

```bash
# Install locust for load testing
pip install locust

# Create locust file for Streamlit app
# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8501
```

### Memory Testing

```bash
# Monitor memory usage during tests
pytest tests/e2e/test_order_management.py::TestPerformance::test_memory_usage_stability -v -s
```

## Common Issues and Solutions

### 1. Playwright Browser Not Found

```bash
# Solution: Install browsers
python -m playwright install
```

### 2. Streamlit App Not Starting in Tests

```bash
# Check if port is available
netstat -an | findstr 8502

# Kill existing processes
taskkill /f /im python.exe
```

### 3. Test Database Conflicts

```bash
# Clean test cache
pytest --cache-clear

# Remove pytest cache
rm -rf .pytest_cache/
```

### 4. Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=src:$PYTHONPATH

# Or use pytest with src path
pytest --import-mode=importlib tests/
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Mock External Dependencies**: Use mocks for API calls
3. **Clear Test Names**: Use descriptive test function names
4. **Fast Tests**: Keep unit tests fast, mark slow tests
5. **Reliable E2E Tests**: Use explicit waits, not sleeps
6. **Test Data**: Use factories for consistent test data
7. **Error Testing**: Test error conditions and edge cases

## Test Maintenance

### Updating Tests for New Features

1. Add unit tests for new functions
2. Update integration tests for new API endpoints
3. Add E2E tests for new UI components
4. Update mock data as needed

### Regular Test Health Checks

```bash
# Run full test suite
pytest tests/ -v

# Check test coverage
pytest --cov=src --cov-report=term-missing

# Run tests in random order to check independence
pip install pytest-randomly
pytest tests/ --randomly-seed=12345
```
