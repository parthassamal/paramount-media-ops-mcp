# 🧪 Testing Guide

Comprehensive unit tests for the Paramount+ Operations Hub full-stack application.

## 📊 Test Coverage

### Backend (Python/FastAPI)
- ✅ **REST API Endpoints** (4 test files, 50+ tests)
  - `/api/jira` - JIRA production tracking
  - `/api/confluence` - Knowledge base
  - `/api/analytics` - Churn intelligence
  - `/api/streaming` - QoE & infrastructure
- ✅ **Server Core** - Health checks, resources, tools
- ✅ **Error Handling** - 404, 500, validation errors
- ✅ **Response Schemas** - Pydantic validation

### Frontend (React/TypeScript)
- ✅ **API Client** - mcpClient.ts (fetch logic, error handling)
- ✅ **Components** - ProductionTracking (loading, error, data states)
- ✅ **Test Configuration** - Vitest + React Testing Library

---

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Option A: Run the install script
./scripts/install_test_dependencies.sh

# Option B: Install manually
# Backend
cd /Users/psama0214/Hackathon-AI/paramount-media-ops-mcp
source venv/bin/activate
pip install pytest pytest-cov pytest-asyncio httpx

# Frontend
cd dashboard
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

### 2. Run All Tests

```bash
# Run everything
./scripts/run_all_tests.sh

# Or run separately:
# Backend only
pytest

# Frontend only
cd dashboard && npm test
```

---

## 📁 Test Structure

```
paramount-media-ops-mcp/
├── tests/                          # Backend tests
│   ├── test_server.py              # Server core tests
│   ├── test_api_jira.py            # JIRA API tests
│   ├── test_api_confluence.py      # Confluence API tests
│   ├── test_api_analytics.py       # Analytics API tests
│   ├── test_api_streaming.py       # Streaming API tests
│   └── test_integrations.py        # Existing integration tests
├── dashboard/
│   └── src/
│       ├── api/__tests__/
│       │   └── mcpClient.test.ts   # API client tests
│       └── app/components/__tests__/
│           └── ProductionTracking.test.tsx  # Component tests
├── pytest.ini                      # Pytest configuration
├── .coveragerc                     # Coverage configuration
└── vitest.config.ts                # Vitest configuration
```

---

## 🧪 Backend Tests

### Running Tests

```bash
cd /Users/psama0214/Hackathon-AI/paramount-media-ops-mcp
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_api_jira.py

# Run with coverage
pytest --cov=mcp --cov-report=html

# Run specific test class
pytest tests/test_api_jira.py::TestJiraAPIEndpoints

# Run specific test
pytest tests/test_api_jira.py::TestJiraAPIEndpoints::test_get_jira_issues_success

# Run with verbose output
pytest -v

# Run only fast tests (exclude slow)
pytest -m "not slow"
```

### Test Categories

```python
# Mark tests
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
```

### Example Test

```python
def test_get_jira_issues_success():
    """Test successful retrieval of JIRA issues."""
    response = client.get("/api/jira/issues")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 0:
        issue = data[0]
        assert "id" in issue
        assert "summary" in issue
```

---

## 🎨 Frontend Tests

### Running Tests

```bash
cd dashboard

# Run all tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Test Structure

```typescript
describe('ProductionTracking', () => {
  it('should render loading state initially', () => {
    render(<ProductionTracking />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should render production issues when loaded', async () => {
    const mockIssues = [{ id: 'PROD-001', summary: 'Test' }];
    mcpClient.getProductionIssues.mockResolvedValue(mockIssues);
    
    render(<ProductionTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });
  });
});
```

---

## 📈 Coverage Reports

### Backend Coverage

```bash
# Generate coverage report
pytest --cov=mcp --cov-report=html

# Open report
open htmlcov/index.html
```

**Target:** 80%+ coverage

**Excludes:**
- Test files
- Mock data generators
- Migration scripts
- `__pycache__`

### Frontend Coverage

```bash
# Generate coverage report
cd dashboard
npm run test:coverage

# Open report
open coverage/index.html
```

**Target:** 70%+ coverage

**Excludes:**
- Test files
- Config files
- Type definitions
- `node_modules`

---

## 🎯 Test Examples

### Backend API Test

```python
class TestJiraAPIEndpoints:
    def test_create_jira_issue_success(self):
        """Test creating a new JIRA issue."""
        new_issue = {
            "project_key": "PROD",
            "summary": "Test issue",
            "description": "Test description",
            "severity": "Medium"
        }
        
        response = client.post("/api/jira/issues", json=new_issue)
        
        assert response.status_code == 201
        created_issue = response.json()
        assert created_issue["summary"] == new_issue["summary"]
```

### Frontend Component Test

```typescript
it('should display cost impact', async () => {
  const mockIssues = [{
    id: 'PROD-001',
    cost_impact: 75000
  }];
  
  mcpClient.getProductionIssues.mockResolvedValue(mockIssues);
  render(<ProductionTracking />);
  
  await waitFor(() => {
    expect(screen.getByText(/\$75,000/)).toBeInTheDocument();
  });
});
```

### API Client Test

```typescript
describe('mcpClient', () => {
  it('should fetch production issues', async () => {
    const mockIssues = [{ id: 'PROD-001' }];
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockIssues
    });
    
    const issues = await mcpClient.getProductionIssues();
    
    expect(issues).toEqual(mockIssues);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/jira/issues')
    );
  });
});
```

---

## 🐛 Common Issues

### Issue: `ModuleNotFoundError`
**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: `Cannot find module 'vitest'`
**Solution:**
```bash
cd dashboard
npm install --save-dev vitest @testing-library/react
```

### Issue: Tests fail in mock mode
**Solution:** Ensure `MOCK_MODE=true` in `.env`

### Issue: Frontend tests timeout
**Solution:** Increase timeout in `vitest.config.ts`:
```typescript
test: {
  testTimeout: 10000
}
```

---

## 📊 Test Statistics

### Backend
- **Total Tests:** 82
- **API Tests:** 50+
- **Integration Tests:** 27
- **Server Tests:** 15+

### Frontend
- **Component Tests:** 10+
- **API Client Tests:** 8+
- **Total Tests:** 18+

### Combined
- **Total:** 100+ tests
- **Coverage Goal:** 75%+
- **Execution Time:** < 30 seconds

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=mcp --cov-report=xml
      - uses: codecov/codecov-action@v2

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: cd dashboard && npm install
      - run: cd dashboard && npm test -- --coverage
```

---

## 📝 Best Practices

### Backend
1. ✅ Use `TestClient` for API tests
2. ✅ Test both success and error cases
3. ✅ Validate response schemas
4. ✅ Mock external API calls
5. ✅ Use fixtures for common setup

### Frontend
1. ✅ Test user interactions
2. ✅ Test loading/error states
3. ✅ Mock API calls
4. ✅ Use `waitFor` for async operations
5. ✅ Test accessibility

---

## 🎉 Next Steps

1. **Run all tests:**
   ```bash
   ./scripts/run_all_tests.sh
   ```

2. **Check coverage:**
   ```bash
   open htmlcov/index.html
   open dashboard/coverage/index.html
   ```

3. **Add more tests:**
   - Integration clients
   - More components
   - Edge cases

4. **Integrate with CI/CD:**
   - GitHub Actions
   - Pre-commit hooks
   - Coverage reporting

---

**🏆 You now have a comprehensive test suite!**

For questions or issues, check the test files for examples.


