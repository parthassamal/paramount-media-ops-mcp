# Paramount Media Operations MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-0.9.0-orange.svg)](https://github.com/anthropics/mcp)

AI-driven streaming operations platform unifying JIRA production, email complaints, churn analytics, and content ROI via MCP server. Pareto analysis (20% of issues drive 80% of impact) + LLM cross-functional reasoning. $750M/year addressable opportunity.

## 🎯 Overview

This MCP (Model Context Protocol) server provides Claude and other LLMs with access to streaming operations intelligence across:

- **Churn Analysis**: At-risk subscriber cohorts and retention signals
- **Complaint Intelligence**: NLP-clustered support themes driving churn
- **Production Operations**: JIRA-style delays, costs, and risk assessment
- **Content Performance**: Show metrics, ROI, and optimization opportunities
- **Financial Impact**: Revenue correlations and recovery projections

**Key Innovation**: Pareto analysis built-in — automatically identifies the vital 20% of issues driving 80% of impact.

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Running the Server

```bash
# Start MCP server
python -m mcp.server

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Quick Test

```bash
# Validate all components
python validate.py

# Check health
curl http://localhost:8000/health

# List resources
curl http://localhost:8000/resources

# Query churn signals
curl -X POST http://localhost:8000/resources/churn_signals/query \
  -H "Content-Type: application/json" \
  -d '{"risk_threshold": 0.5}'
```

## 📊 Architecture

```
paramount-media-ops-mcp/
├── mcp/
│   ├── server.py              # FastAPI MCP server
│   ├── resources/             # 9 data resources
│   │   ├── churn_signals.py
│   │   ├── complaints_topics.py
│   │   ├── production_issues.py
│   │   ├── content_catalog.py
│   │   └── ...
│   ├── tools/                 # 5 LLM-callable tools
│   │   ├── analyze_churn_root_cause.py
│   │   ├── analyze_complaint_themes.py
│   │   └── ...
│   ├── integrations/          # Data connectors
│   │   ├── jira_connector.py
│   │   ├── email_parser.py
│   │   └── ...
│   ├── pareto/                # Pareto analysis engine
│   │   ├── pareto_calculator.py
│   │   └── pareto_insights.py
│   └── mocks/                 # Mock data generators
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
└── validate.py                # Validation script
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Server
MCP_SERVER_PORT=8000
ENVIRONMENT=development

# Mock mode (set false for production APIs)
MOCK_MODE=true

# External APIs (when MOCK_MODE=false)
JIRA_API_TOKEN=your_token
ANALYTICS_API_KEY=your_key
# ... (see .env.example for all options)
```

## 📚 Resources (Data Endpoints)

Nine resources provide comprehensive operations intelligence:

| Resource | Description | Key Metrics |
|----------|-------------|-------------|
| `churn_signals` | At-risk subscriber cohorts | Risk scores, LTV, financial impact |
| `complaints_topics` | NLP-clustered support themes | Sentiment, churn correlation |
| `production_issues` | Delays and cost overruns | Delay days, budget impact |
| `content_catalog` | Show performance metrics | Viewing hours, completion rates |
| `international_markets` | Regional performance | Geographic gaps, expansion opportunities |
| `revenue_impact` | Financial correlations | Addressable losses, ROI projections |
| `retention_campaigns` | Campaign tracking | Conversion rates, effectiveness scores |
| `operational_efficiency` | Production metrics | On-time rate, resource utilization |
| `pareto_analysis` | 80/20 decomposition | Cross-dimensional Pareto validation |

See [docs/RESOURCES.md](docs/RESOURCES.md) for detailed documentation.

## 🛠️ Tools (LLM-Callable Actions)

Five tools provide actionable analysis:

| Tool | Purpose | Returns |
|------|---------|---------|
| `analyze_churn_root_cause` | Correlate churn with complaints + production | Root causes with evidence and recommendations |
| `analyze_complaint_themes` | Extract fixable high-impact themes | Prioritized roadmap by complexity vs impact |
| `analyze_production_risk` | Identify critical 20% of issues | Risk assessment with mitigation plans |
| `forecast_revenue_with_constraints` | Project recovery under budget limits | Scenario-based revenue forecasts |
| `generate_retention_campaign` | Create targeted retention campaign | Complete campaign plan with projections |

See [docs/TOOLS.md](docs/TOOLS.md) for detailed documentation.

## 🎓 Usage Examples

### Query Resource (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/resources/churn_signals/query",
    json={"risk_threshold": 0.7, "include_pareto": True}
)

data = response.json()
print(f"At-risk subscribers: {data['data']['result']['retention_metrics']['total_at_risk_30d']}")
```

### Execute Tool (Python)

```python
response = requests.post(
    "http://localhost:8000/tools/analyze_churn_root_cause/execute",
    json={"cohort_id": "COHORT-001", "include_recommendations": True}
)

analysis = response.json()
print(analysis['data']['result']['recommendations'])
```

### MCP Protocol Format

```json
// Query resource
{
  "resource": "churn_signals",
  "params": {
    "risk_threshold": 0.7,
    "include_pareto": true
  }
}

// Execute tool
{
  "tool": "analyze_churn_root_cause",
  "params": {
    "cohort_id": "COHORT-001"
  }
}
```

See [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) for more examples.

## 🤖 Claude Integration

See [docs/INTEGRATION.md](docs/INTEGRATION.md) for detailed integration guide.

**Quick Claude Prompt:**

```
You are connected to the Paramount Media Operations MCP server at http://localhost:8000.

Available resources:
- churn_signals: Query at-risk subscriber cohorts
- complaints_topics: Analyze customer complaint themes
- production_issues: Review production delays and costs

Available tools:
- analyze_churn_root_cause: Find why subscribers are churning
- analyze_complaint_themes: Prioritize fixable issues

Use POST to /resources/{name}/query to get data.
Use POST to /tools/{name}/execute to run analysis.

Task: Identify the top 3 drivers of subscriber churn and recommend actions.
```

## 📈 Pareto Analysis

All mock data follows Pareto distribution where top 20% drives 75-85% of impact:

- **Churn**: Top cohort drives 77% of financial impact ✅
- **Production**: Top 4 issues drive 70%+ of delays
- **Complaints**: Top 2 themes drive 64% of churn-related complaints
- **Content**: Top 20% of shows drive 61% of viewing hours

Run `python validate.py` to verify Pareto validation.

## 🧪 Testing

```bash
# Run validation
python validate.py

# Test specific resource
python -c "from mcp.resources import create_churn_signals; print(create_churn_signals().query())"

# Test specific tool
python -c "from mcp.tools import create_analyze_churn; print(create_analyze_churn().execute())"
```

## 🔐 Security

- No hardcoded credentials (use `.env`)
- Mock mode prevents accidental API calls
- Structured logging with privacy controls
- Input validation via Pydantic models

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/parthassamal/paramount-media-ops-mcp/issues)
- API Docs: http://localhost:8000/docs (when server running)

---

**Built for the 48-hour hackathon** | **Production-ready foundation** | **Immediately extensible**

