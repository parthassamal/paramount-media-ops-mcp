# Complete Integration Setup Guide

## 🔌 Third-Party API Integration

This guide will walk you through setting up **real integrations** with Conviva, NewRelic, and Atlassian (JIRA/Confluence) to replace mock data with live operational data.

---

## 🎯 Overview

The MCP server supports three modes:

1. **Mock Mode** (Default) - Uses generated data, perfect for demos
2. **Hybrid Mode** - Mix of live and mock data (recommended for hackathons)
3. **Full Integration Mode** - All live data from real APIs

---

## 📋 Prerequisites

Before you begin, you'll need:

- [ ] Conviva account and API access
- [ ] NewRelic account (free tier available)
- [ ] Atlassian Cloud account (free for small teams)
- [ ] Admin access to create API tokens
- [ ] Python 3.10+ installed

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Copy Environment Template

```bash
cd paramount-media-ops-mcp
cp .env.example .env
```

### Step 2: Run Setup Script

```bash
python scripts/setup_integrations.py
```

This interactive script will:
- Guide you through API key creation
- Test connections
- Update your `.env` file
- Validate configurations

---

## 🔑 Conviva Integration

### What You'll Get

- Real-time Quality of Experience (QoE) metrics
- Buffering ratio, video start failures, concurrent plays
- CDN performance data
- Device and geography breakdowns

### Setup Steps

#### 1. Create Conviva API Credentials

1. **Log in to Conviva Pulse**: https://pulse.conviva.com
2. **Navigate to Settings** → API Keys
3. **Create New API Key**:
   - Name: "Paramount MCP Server"
   - Permissions: Read-only access
   - Scope: Insights API

4. **Copy Your Credentials**:
   - Customer Key (e.g., `c3.customer_name`)
   - API Key (long alphanumeric string)

#### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Conviva Configuration
CONVIVA_ENABLED=true
CONVIVA_API_URL=https://api.conviva.com/insights/2.4
CONVIVA_CUSTOMER_KEY=c3.your_customer_name
CONVIVA_API_KEY=your_api_key_here

# Optional: Conviva Settings
CONVIVA_DEFAULT_FILTER=account:Paramount+
CONVIVA_CACHE_TTL_SECONDS=300
```

#### 3. Test Connection

```bash
python scripts/test_integrations.py --service conviva
```

**Expected Output:**
```
✅ Conviva Connection Test
   Status: Connected
   Account: Paramount+
   Metrics Available: plays, buffering_ratio, vsf, ebvs
   Sample Data:
     - Concurrent Plays: 125,430
     - Buffering Ratio: 2.1%
     - Average Bitrate: 2,450 kbps
```

---

## 📊 NewRelic Integration

### What You'll Get

- Application Performance Monitoring (APM)
- Response times, error rates, throughput
- Infrastructure health metrics
- Transaction tracing

### Setup Steps

#### 1. Create NewRelic API Key

1. **Log in to NewRelic**: https://one.newrelic.com
2. **Navigate to** → Account Settings → API Keys
3. **Create User Key**:
   - Key Type: User Key
   - Name: "Paramount MCP Server"
   - Notes: "For MCP server integration"

4. **Copy Your Key**: Starts with `NRAK-`

5. **Find Your Account ID**:
   - Click on your account name (top right)
   - Account ID shown in URL or account dropdown

#### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# NewRelic Configuration
NEWRELIC_ENABLED=true
NEWRELIC_API_URL=https://api.newrelic.com/graphql
NEWRELIC_API_KEY=NRAK-YOUR_API_KEY_HERE
NEWRELIC_ACCOUNT_ID=1234567

# Optional: NewRelic Settings
NEWRELIC_APP_NAME=Paramount+
NEWRELIC_CACHE_TTL_SECONDS=300
```

#### 3. Test Connection

```bash
python scripts/test_integrations.py --service newrelic
```

**Expected Output:**
```
✅ NewRelic Connection Test
   Status: Connected
   Account ID: 1234567
   Monitored Applications: 3
   Sample Metrics:
     - Response Time (avg): 145ms
     - Response Time (p95): 320ms
     - Error Rate: 0.12%
     - Apdex Score: 0.94
```

---

## 📋 Atlassian (JIRA/Confluence) Integration

### What You'll Get

- Live production issues from JIRA
- Operational runbooks from Confluence
- Issue tracking and workflow management
- Team collaboration data

### Setup Steps

#### 1. Create Atlassian API Token

1. **Log in to Atlassian**: https://id.atlassian.com
2. **Navigate to Security**: https://id.atlassian.com/manage-profile/security/api-tokens
3. **Create API Token**:
   - Label: "Paramount MCP Server"
   - Click "Create"
   - **Copy the token immediately** (won't be shown again)

#### 2. Find Your Site URL

Your Atlassian site URL format: `https://YOUR-DOMAIN.atlassian.net`

Example: `https://paramounthackathon.atlassian.net`

#### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# JIRA Configuration
JIRA_ENABLED=true
JIRA_FORCE_LIVE=true
JIRA_API_URL=https://your-domain.atlassian.net
JIRA_API_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_atlassian_api_token
JIRA_PROJECT_KEY=PROD

# Confluence Configuration
CONFLUENCE_ENABLED=true
CONFLUENCE_API_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your_atlassian_api_token
CONFLUENCE_SPACE_KEY=OPS
```

#### 4. Test Connection

```bash
python scripts/test_integrations.py --service jira
python scripts/test_integrations.py --service confluence
```

**Expected Output:**
```
✅ JIRA Connection Test
   Status: Connected
   Project: PROD (Production Issues)
   Open Issues: 24
   Critical Issues: 3
   Sample Issue: PROD-8472 - Payment processing failures

✅ Confluence Connection Test
   Status: Connected
   Space: OPS (Operations)
   Pages: 15
   Recent Page: Production Incident Response Runbook
```

---

## 🔄 Integration Modes

### Mode 1: Full Mock (Default)

```bash
# .env
MOCK_MODE=true
CONVIVA_ENABLED=false
NEWRELIC_ENABLED=false
JIRA_ENABLED=false
```

**Use Case**: Demos, development, testing

### Mode 2: Hybrid (Recommended for Hackathon)

```bash
# .env
MOCK_MODE=true          # Keep mock data for stability
JIRA_FORCE_LIVE=true    # But use live JIRA
JIRA_ENABLED=true
CONVIVA_ENABLED=false   # Keep these mocked
NEWRELIC_ENABLED=false
```

**Use Case**: Hackathons, presentations with some live data

### Mode 3: Full Integration

```bash
# .env
MOCK_MODE=false
CONVIVA_ENABLED=true
NEWRELIC_ENABLED=true
JIRA_ENABLED=true
CONFLUENCE_ENABLED=true
```

**Use Case**: Production, real operations

---

## 🛠️ Helper Scripts

### 1. Interactive Setup Script

```bash
python scripts/setup_integrations.py
```

**Features:**
- Interactive prompts for API keys
- Connection validation
- Automatic `.env` file creation
- Health checks

### 2. Integration Testing Script

```bash
# Test all integrations
python scripts/test_integrations.py --all

# Test specific service
python scripts/test_integrations.py --service conviva
python scripts/test_integrations.py --service newrelic
python scripts/test_integrations.py --service jira

# Verbose mode
python scripts/test_integrations.py --all --verbose
```

### 3. Health Check Script

```bash
python scripts/health_check.py
```

**Output:**
```
🏥 INTEGRATION HEALTH CHECK

✅ Conviva: Connected (2.1s response time)
✅ NewRelic: Connected (1.5s response time)
✅ JIRA: Connected (0.8s response time)
✅ Confluence: Connected (1.2s response time)

📊 Overall Status: All Systems Operational
```

---

## 🎯 API Key Management Best Practices

### Security

1. **Never commit API keys to git**:
   ```bash
   # Already in .gitignore
   .env
   .env.local
   *.key
   ```

2. **Use environment variables**:
   ```bash
   export CONVIVA_API_KEY="your-key"
   python -m mcp.server
   ```

3. **Rotate keys regularly**:
   - Set calendar reminder for quarterly rotation
   - Use descriptive key names with dates

4. **Use read-only permissions**:
   - MCP server only needs read access
   - Never use admin keys

### Key Storage

1. **Development**: `.env` file (gitignored)
2. **Production**: Environment variables or secret manager
3. **CI/CD**: GitHub Secrets, AWS Secrets Manager, etc.

---

## 🔍 Troubleshooting

### Conviva Connection Issues

**Problem**: `401 Unauthorized`
```
Solution:
1. Verify Customer Key format: c3.customer_name
2. Check API Key is correct (no spaces)
3. Ensure API key has Insights API access
```

**Problem**: `No data returned`
```
Solution:
1. Check date range in filter
2. Verify account name matches
3. Ensure you have active streams
```

### NewRelic Connection Issues

**Problem**: `403 Forbidden`
```
Solution:
1. Verify API key starts with NRAK-
2. Check account ID is correct
3. Ensure key has query permissions
```

**Problem**: `No applications found`
```
Solution:
1. Verify you have APM agent installed
2. Check application name filter
3. Ensure data is being reported
```

### JIRA/Confluence Issues

**Problem**: `Authentication failed`
```
Solution:
1. Verify email address is correct
2. Check API token (copy without spaces)
3. Ensure token hasn't expired
4. Try logging in to web interface first
```

**Problem**: `Project not found`
```
Solution:
1. Check project key is correct (case-sensitive)
2. Verify you have access to the project
3. Ensure project exists
```

---

## 📊 Validation Checklist

Use this checklist to ensure everything is configured correctly:

### Pre-Flight Checks

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created

### Conviva Setup

- [ ] Account created
- [ ] API key generated
- [ ] Customer key copied
- [ ] Environment variables set
- [ ] Connection test passed

### NewRelic Setup

- [ ] Account created (free tier OK)
- [ ] User API key generated
- [ ] Account ID obtained
- [ ] Environment variables set
- [ ] Connection test passed

### JIRA/Confluence Setup

- [ ] Atlassian account created
- [ ] API token generated
- [ ] Site URL confirmed
- [ ] Project/Space created
- [ ] Environment variables set
- [ ] Connection tests passed

### Final Validation

- [ ] All health checks pass
- [ ] Server starts without errors
- [ ] API endpoints return real data
- [ ] Dashboard shows live metrics

---

## 🎬 Demo Workflow

For hackathon presentations, use this workflow:

### 1. Pre-Demo Setup (5 minutes before)

```bash
# Start server in hybrid mode
python -m mcp.server

# Verify health
curl http://localhost:8000/health

# Check integration status
python scripts/health_check.py
```

### 2. During Demo

**Show Live Data**:
```bash
# Query live JIRA issues
curl -X POST http://localhost:8000/api/jira/issues

# Show real production tracking
# Dashboard shows "Live" indicator
```

**Fallback to Mock**:
- If API has issues, set `MOCK_MODE=true`
- Server automatically falls back
- Demo continues seamlessly

### 3. Talking Points

- "We're integrated with **real production systems**"
- "This JIRA data is **live** from our Atlassian instance"
- "Streaming metrics from **actual CDN** (or simulated if demo)"
- "AI analyzes **real patterns** in production issues"

---

## 📈 Cost Breakdown

### Free Tier Options

| Service | Free Tier | Sufficient For |
|---------|-----------|----------------|
| **NewRelic** | 100GB/month | ✅ Demo, small production |
| **Atlassian** | 10 users | ✅ Team collaboration |
| **Conviva** | Trial account | ⚠️ Contact sales |

### Estimated Costs (Production)

| Service | Monthly Cost | What You Get |
|---------|--------------|--------------|
| Conviva | $500-2000+ | Full QoE monitoring |
| NewRelic | $0-100 | APM (free tier + buffer) |
| Atlassian | $0-70 | Free for <10 users |
| **Total** | **$500-2170** | Full integration |

---

## 🚀 Next Steps

1. **Run Setup Script**:
   ```bash
   python scripts/setup_integrations.py
   ```

2. **Test Connections**:
   ```bash
   python scripts/test_integrations.py --all
   ```

3. **Start Server**:
   ```bash
   python -m mcp.server
   ```

4. **Verify Integration**:
   - Open http://localhost:8000/docs
   - Try API endpoints
   - Check dashboard

5. **Run Demo**:
   ```bash
   python demo_usage.py
   ```

---

## 📚 Additional Resources

- [Conviva API Documentation](https://developer.conviva.com/)
- [NewRelic API Guide](https://docs.newrelic.com/docs/apis/intro-apis/introduction-new-relic-apis/)
- [Atlassian API Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Environment Variables Guide](./docs/CONFIGURATION.md)

---

## 🆘 Support

If you encounter issues:

1. Check troubleshooting section above
2. Run health check: `python scripts/health_check.py`
3. Check logs: `tail -f logs/mcp_server.log`
4. Review API provider status pages
5. Open GitHub issue with error details

---

<div align="center">

**🔌 Ready to integrate? Run the setup script!**

```bash
python scripts/setup_integrations.py
```

**Built with ❤️ for Paramount+ Operations Excellence**

</div>

