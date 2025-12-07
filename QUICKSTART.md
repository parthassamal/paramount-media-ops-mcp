# Quick Start Guide - Paramount+ MCP Server

## 5-Minute Setup

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/parthassamal/paramount-media-ops-mcp.git
cd paramount-media-ops-mcp

# Install dependencies
pip install -r requirements.txt
```

### 2. Test the System

Run the example demonstration:

```bash
python example_usage.py
```

You should see a complete demonstration of:
- Churn analysis with Pareto insights
- Production issue prioritization
- Complaint theme analysis with NLP
- Content ROI optimization
- Executive summary with strategic recommendations

### 3. Start the MCP Server

```bash
python -m src.server
```

The server will start in stdio mode, ready to accept MCP protocol commands.

### 4. Connect with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "paramount-ops": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/paramount-media-ops-mcp"
    }
  }
}
```

Replace `/absolute/path/to/paramount-media-ops-mcp` with your actual path.

### 5. Test with Claude

Once connected, you can ask Claude:

- "Show me the current churn signals"
- "Analyze production issues using Pareto principle"
- "What are the top complaint topics?"
- "Forecast revenue for the next 12 months"
- "Generate a retention campaign for high-risk users"

## Available Resources

Ask Claude to read any of these resources:

- `paramount://churn_signals` - User churn risk data
- `paramount://complaints_topics` - Customer complaints with NLP analysis
- `paramount://production_issues` - JIRA production issues
- `paramount://content_catalog` - Content performance and ROI
- `paramount://international_markets` - Market-specific data
- `paramount://revenue_analytics` - Revenue and subscription metrics
- `paramount://engagement_metrics` - User engagement patterns
- `paramount://pareto_insights` - Cross-domain 80/20 insights
- `paramount://operational_dashboard` - Real-time KPIs

## Available Tools

Ask Claude to use these analysis tools:

1. **analyze_churn_root_cause** - Identify why users are churning
2. **analyze_complaint_themes** - Understand customer pain points
3. **analyze_production_risk** - Assess system health and prioritize fixes
4. **forecast_revenue_with_constraints** - Project future revenue
5. **generate_retention_campaign** - Create targeted retention strategies

## Optional: JIRA Integration

To connect to real JIRA data:

```bash
export JIRA_SERVER="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-api-token"
```

Without these credentials, the system uses realistic mock data.

## Example Queries for Claude

Try these with Claude once the MCP server is connected:

1. **Strategic Overview**:
   "Read the pareto_insights resource and give me the top priorities for this quarter"

2. **Churn Analysis**:
   "Analyze churn root causes for premium users over the last 60 days"

3. **Production Crisis**:
   "Analyze production risk with severity threshold High and tell me what to fix first"

4. **Customer Satisfaction**:
   "Analyze complaint themes with urgency filter Critical and show sentiment trends"

5. **Financial Planning**:
   "Forecast revenue for 12 months in an optimistic scenario with max churn rate of 0.04"

6. **Marketing Campaign**:
   "Generate a retention campaign for high_risk segment with $200,000 budget using email and push channels"

## Troubleshooting

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Server Won't Start
Check Python version:
```bash
python --version  # Should be 3.10+
```

### JIRA Connection Issues
The system automatically falls back to mock data if JIRA credentials are invalid or not provided.

## Next Steps

1. Explore the `example_usage.py` script to understand the data structures
2. Read the full README.md for detailed documentation
3. Check `src/` directory for implementation details
4. Customize mock data generators in `src/mock_data.py` for your use cases

## Support

For issues or questions, please open an issue on GitHub or contact the development team.

---

**Ready in 5 minutes. Unlocking $750M in operational value!** 🚀
