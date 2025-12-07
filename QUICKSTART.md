# Quick Start Guide - Paramount+ MCP Server

## ⚡ 5-Minute Setup

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Validate Installation

```bash
python demo_usage.py
```

You should see a complete demonstration of:
- ✅ Churn analysis with Pareto insights
- ✅ Production issue prioritization
- ✅ Complaint theme analysis with NLP
- ✅ Campaign generation with ROI projections
- ✅ Executive summary with strategic recommendations

### 3. Start the MCP Server

```bash
python -m mcp.server
```

The server will start on `http://localhost:8000`.

### 4. Verify Server Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "server_name": "paramount-media-ops-mcp",
    "version": "0.1.0"
  }
}
```

### 5. Explore API Documentation

Open in browser: http://localhost:8000/docs

---

## 🔌 Connect with Claude Desktop

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "paramount-ops": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/absolute/path/to/paramount-media-ops-mcp"
    }
  }
}
```

Replace `/absolute/path/to/paramount-media-ops-mcp` with your actual path.

---

## 📊 Available Resources

Ask Claude to read any of these resources:

| Resource | Description |
|----------|-------------|
| `churn_signals` | At-risk subscriber cohorts with Pareto analysis |
| `complaints_topics` | NLP-analyzed customer complaints |
| `production_issues` | JIRA production issues with cost/delay impact |
| `content_catalog` | Content performance and ROI metrics |
| `international_markets` | Regional market performance data |
| `revenue_impact` | Financial correlations and projections |
| `retention_campaigns` | Campaign tracking and performance |
| `operational_efficiency` | Production pipeline metrics |
| `pareto_analysis` | Cross-domain 80/20 insights |

---

## 🛠️ Available Tools

Ask Claude to use these analysis tools:

| Tool | Description |
|------|-------------|
| `analyze_churn_root_cause` | Identify why users are churning |
| `analyze_complaint_themes` | Understand customer pain points |
| `analyze_production_risk` | Assess system health, prioritize fixes |
| `forecast_revenue_with_constraints` | Project future revenue scenarios |
| `generate_retention_campaign` | Create targeted retention strategies |

---

## 💬 Example Queries for Claude

Once the MCP server is connected, try these:

### Strategic Overview
> "Read the pareto_analysis resource and give me the top 3 priorities for this quarter"

### Churn Analysis
> "Analyze churn root causes and tell me which cohort needs immediate attention"

### Production Health
> "Analyze production risk with high severity and recommend what to fix first"

### Customer Satisfaction
> "Analyze complaint themes and show me the quick wins we can fix in 2 weeks"

### Financial Planning
> "Forecast revenue for 12 months with a $10M budget constraint"

### Marketing Campaign
> "Generate a retention campaign for COHORT-001 with $500,000 budget"

---

## ⚙️ Optional: External Integrations

### JIRA Integration
```bash
export JIRA_API_URL="https://your-domain.atlassian.net"
export JIRA_API_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-api-token"
```

### Conviva Integration
```bash
export CONVIVA_API_URL="https://api.conviva.com/insights/2.4"
export CONVIVA_CUSTOMER_KEY="your-customer-key"
export CONVIVA_API_KEY="your-api-key"
```

### NewRelic Integration
```bash
export NEWRELIC_API_URL="https://api.newrelic.com/graphql"
export NEWRELIC_API_KEY="your-api-key"
export NEWRELIC_ACCOUNT_ID="your-account-id"
```

Without these credentials, the system uses **realistic mock data** - perfect for demos!

---

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=mcp --cov-report=term-missing
```

---

## 🔧 Troubleshooting

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Server Won't Start
```bash
# Check Python version (requires 3.10+)
python --version

# Verify installation
python -c "import mcp; print('OK')"
```

### Connection Refused
- Verify server is running on port 8000
- Check firewall settings
- Try `curl http://localhost:8000/health`

### JIRA Connection Issues
The system automatically falls back to mock data if JIRA credentials are invalid or not provided.

---

## 📚 Next Steps

1. Explore the `demo_usage.py` script to understand capabilities
2. Read the full [README.md](./README.md) for detailed documentation
3. Check [docs/INTEGRATION.md](./docs/INTEGRATION.md) for Claude integration
4. Review [docs/API_EXAMPLES.md](./docs/API_EXAMPLES.md) for API usage

---

**Ready in 5 minutes. Unlocking $750M in operational value!** 🚀
