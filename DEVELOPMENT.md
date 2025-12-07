# Development Guide

## Project Structure

```
paramount-media-ops-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # Main MCP server
│   ├── pareto_engine.py       # Pareto analysis implementation
│   ├── jira_connector.py      # JIRA integration
│   ├── email_parser.py        # NLP complaint analysis
│   └── mock_data.py           # Mock data generators
├── tests/
│   ├── __init__.py
│   ├── test_pareto_engine.py
│   ├── test_mock_data.py
│   ├── test_jira_connector.py
│   └── test_email_parser.py
├── .github/
│   └── workflows/
│       └── test.yml           # CI/CD pipeline
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── example_usage.py
├── config.example.py
└── .gitignore
```

## Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp
pip install -r requirements.txt
pip install pytest pytest-asyncio  # For testing
```

### 2. Environment Variables (Optional)

For JIRA integration:

```bash
export JIRA_SERVER="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-api-token"
```

For LLM integration (future):

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_pareto_engine.py -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

### Test the Example

```bash
python example_usage.py
```

## Code Style

### Formatting

```bash
pip install black
black src/ tests/
```

### Linting

```bash
pip install pylint
pylint src/
```

### Type Checking

```bash
pip install mypy
mypy src/ --ignore-missing-imports
```

## Adding New Features

### Adding a New Resource

1. Add resource definition in `server.py` `list_resources()`:

```python
types.Resource(
    uri="paramount://new_resource",
    name="New Resource",
    mimeType="application/json",
    description="Description of the new resource"
)
```

2. Implement resource reader in `read_resource()`:

```python
elif uri == "paramount://new_resource":
    # Your implementation
    return json.dumps(data, indent=2)
```

### Adding a New Tool

1. Add tool definition in `server.py` `list_tools()`:

```python
types.Tool(
    name="new_tool",
    description="What this tool does",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            # More parameters
        }
    }
)
```

2. Implement tool handler in `call_tool()`:

```python
elif name == "new_tool":
    # Your implementation
    result = {"data": "result"}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
```

### Adding New Mock Data

Add generator method to `MockDataGenerator` in `src/mock_data.py`:

```python
@staticmethod
def generate_new_data(count: int = 50) -> List[Dict[str, Any]]:
    """Generate mock data"""
    data = []
    for i in range(count):
        data.append({
            "id": i,
            # Your fields
        })
    return data
```

## Testing Your Changes

### 1. Unit Tests

Add tests in `tests/test_*.py`:

```python
def test_new_feature():
    """Test description"""
    result = your_function()
    assert result is not None
    assert "expected_key" in result
```

### 2. Integration Test

Run the full example:

```bash
python example_usage.py
```

### 3. MCP Server Test

Start the server and verify it loads:

```bash
python -c "from src.server import server; print(server.name)"
```

## Debugging

### Debug Mock Data

```python
from src.mock_data import MockDataGenerator

gen = MockDataGenerator()
data = gen.generate_churn_cohort(10)
print(data)
```

### Debug Pareto Analysis

```python
from src.pareto_engine import ParetoAnalyzer

data = [{"item": "A", "value": 100}, {"item": "B", "value": 50}]
result = ParetoAnalyzer.analyze(data, "value", "item")
print(result)
```

### Debug Server Components

```python
from src.jira_connector import JIRAConnector
from src.email_parser import EmailParser

jira = JIRAConnector()
parser = EmailParser()

issues = jira.fetch_production_issues(10)
complaints = parser.get_mock_complaints(10)
```

## Performance Optimization

### Caching

For expensive operations, consider caching:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param):
    # Your code
    pass
```

### Async Operations

For I/O-bound operations:

```python
import asyncio

async def async_operation():
    # Your async code
    pass
```

## Common Issues

### Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### NLTK Data Missing

If you get NLTK data errors:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

### Mock Data Randomness

For reproducible tests, set random seed:

```python
import random
random.seed(42)
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Format code: `black src/ tests/`
6. Commit: `git commit -am 'Add new feature'`
7. Push: `git push origin feature/new-feature`
8. Create a Pull Request

## Release Process

1. Update version in `config.example.py`
2. Update CHANGELOG (if exists)
3. Run full test suite
4. Tag release: `git tag v1.0.0`
5. Push tags: `git push --tags`

## Architecture Decisions

### Why Pareto Analysis?

The 80/20 rule (Pareto Principle) helps focus on the vital few issues that have the most impact. In operations:
- 20% of issues cause 80% of user impact
- 20% of content drives 80% of engagement
- 20% of markets contribute 80% of revenue

### Why Mock Data by Default?

- Allows testing without external dependencies
- Provides consistent data for demonstrations
- Easy to customize for different scenarios
- Falls back gracefully when credentials aren't available

### Why MCP Protocol?

- Standard protocol for AI-tool integration
- Works seamlessly with Claude Desktop
- Extensible for other AI systems
- Simple stdio transport

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JIRA Python Library](https://jira.readthedocs.io/)
- [TextBlob NLP](https://textblob.readthedocs.io/)

## Support

For questions or issues:
1. Check this guide
2. Review the README.md
3. Look at example_usage.py
4. Open a GitHub issue

---

**Happy coding! Let's unlock that $750M opportunity!** 🚀
