# API Testing Guide

Quick reference for running the comprehensive API test suite.

## Test Files

1. **`tests/test_api_comprehensive.py`** - Full pytest suite (42 tests)
2. **`test_api_http.py`** - HTTP-based tests (28 tests)
3. **`run_api_tests.py`** - Test orchestrator with reporting

## Quick Start

### Option 1: HTTP Tests (Simplest)

```bash
# 1. Start backend server
cd /Users/greenmachine2.0/Craigslist
./start_backend.sh

# 2. Run tests in another terminal
cd backend
python3 test_api_http.py
```

### Option 2: Pytest Suite (Recommended)

```bash
# 1. Install dependencies (one time)
pip install pytest pytest-asyncio pytest-html pytest-json-report httpx

# 2. Run tests
pytest tests/test_api_comprehensive.py -v

# 3. With HTML report
pytest tests/test_api_comprehensive.py --html=test_report.html --self-contained-html
```

### Option 3: Full Test Run with Reporting

```bash
# Requires pytest-json-report and pytest-html
pip install pytest-json-report pytest-html

python3 run_api_tests.py
```

## Test Coverage

### 1. Auto-Response Templates (`/api/v1/templates/*`)
- ✓ Create template
- ✓ List templates with filters
- ✓ Get template by ID
- ✓ Update template
- ✓ Delete template
- ✓ A/B testing analytics
- ✓ Template preview

### 2. Email Tracking (`/api/v1/tracking/*`)
- ✓ Track email opens
- ✓ Track email clicks
- ✓ Unsubscribe handling
- ✓ Unsubscribe confirmation page

### 3. Demo Site Builder (`/api/v1/demo-sites/*`)
- ✓ Generate demo site
- ✓ List demo sites with pagination
- ✓ Get demo site details
- ✓ Update demo site
- ✓ Delete demo site
- ✓ Preview demo site
- ✓ Export demo site files
- ✓ Duplicate demo site
- ✓ List templates
- ✓ Template CRUD
- ✓ Component library

### 4. N8N Workflows (`/api/v1/webhooks/n8n/*` and `/api/v1/workflows/approvals/*`)
- ✓ Webhook connectivity
- ✓ Receive webhooks
- ✓ Create approval requests
- ✓ List pending approvals
- ✓ Submit approval decisions
- ✓ Escalate approvals
- ✓ Bulk approve
- ✓ Approval statistics
- ✓ Auto-approval rules
- ✓ Rule templates

## Test by Endpoint Group

```bash
# Templates only
pytest tests/test_api_comprehensive.py::TestTemplatesAPI -v

# Email tracking only
pytest tests/test_api_comprehensive.py::TestEmailTrackingAPI -v

# Demo sites only
pytest tests/test_api_comprehensive.py::TestDemoSitesAPI -v

# Workflows only
pytest tests/test_api_comprehensive.py::TestN8NWebhooksAPI -v
pytest tests/test_api_comprehensive.py::TestWorkflowApprovalsAPI -v

# Edge cases
pytest tests/test_api_comprehensive.py::TestEdgeCases -v

# Performance tests
pytest tests/test_api_comprehensive.py::TestPerformance -v
```

## Expected Results

### Success Criteria
- **Templates API**: 8-12 tests passing
- **Email Tracking API**: 3-4 tests passing
- **Demo Sites API**: 10-15 tests passing
- **Workflows API**: 8-14 tests passing

### Known Limitations
- Some tests may skip if database models are not fully implemented
- Auto-response endpoints require `AutoResponse` model
- Response variable endpoints require `ResponseVariable` model
- Background tasks tests may fail if services are not running

## Troubleshooting

### Server Not Running
```bash
Error: Server not reachable at http://localhost:8000

Solution:
cd /Users/greenmachine2.0/Craigslist
./start_backend.sh
```

### Missing Dependencies
```bash
ModuleNotFoundError: No module named 'pytest'

Solution:
pip install pytest pytest-asyncio httpx requests
```

### Database Connection Errors
```bash
sqlalchemy.exc.OperationalError: could not connect to server

Solution:
# Check PostgreSQL is running
pg_ctl status

# Or use Docker
docker-compose up -d postgres
```

### Import Errors
```bash
ImportError: cannot import name 'app' from 'app.main'

Solution:
# Ensure you're in the backend directory
cd /Users/greenmachine2.0/Craigslist/backend
export PYTHONPATH=/Users/greenmachine2.0/Craigslist/backend:$PYTHONPATH
```

## Test Reports

### JSON Report
```bash
pytest tests/test_api_comprehensive.py --json-report --json-report-file=test_results.json
```

### HTML Report
```bash
pytest tests/test_api_comprehensive.py --html=test_report.html --self-contained-html
open test_report.html
```

### Coverage Report
```bash
pip install pytest-cov
pytest tests/test_api_comprehensive.py --cov=app.api.endpoints --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-html httpx
      - name: Run tests
        run: pytest tests/test_api_comprehensive.py -v --html=test_report.html
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_report.html
```

## Performance Benchmarks

| Operation | Expected Time | Maximum |
|-----------|---------------|---------|
| List Templates | < 0.5s | 1.0s |
| Create Template | < 1.0s | 2.0s |
| Generate Demo Site | < 5.0s | 10.0s |
| Track Email Open | < 0.2s | 0.5s |
| Process Webhook | < 0.5s | 1.0s |

## Next Steps

1. ✓ Run test suite to verify all endpoints
2. ✓ Review test report for failures
3. Address any failing tests
4. Implement missing models (AutoResponse, ResponseVariable)
5. Add authentication middleware
6. Set up CI/CD pipeline
7. Add load testing with locust/k6

## Additional Resources

- **Full Test Report**: `API_TEST_REPORT.md`
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

**Test Suite Version**: 1.0
**Last Updated**: November 5, 2025
**Maintainer**: Development Team
