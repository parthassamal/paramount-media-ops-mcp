# API Keys Quick Reference Card

## 🔑 Where to Get Your API Keys

### Conviva

**URL**: https://pulse.conviva.com

**Steps**:
1. Log in to Conviva Pulse
2. Settings → API Keys
3. Create New API Key
4. Copy **Customer Key** (format: `c3.company_name`)
5. Copy **API Key**

**Free Tier**: ❌ Contact sales for trial
**Cost**: $500-2000+/month

---

### NewRelic

**URL**: https://one.newrelic.com

**Steps**:
1. Log in to NewRelic One
2. Account Settings → API Keys
3. Create User Key
4. Copy **API Key** (starts with `NRAK-`)
5. Note your **Account ID** (in account dropdown)

**Free Tier**: ✅ 100GB/month
**Cost**: $0-100/month

---

### Atlassian (JIRA + Confluence)

**URL**: https://id.atlassian.com/manage-profile/security/api-tokens

**Steps**:
1. Log in to Atlassian
2. Security → API Tokens
3. Create API Token
4. Label: "Paramount MCP Server"
5. Copy **API Token** immediately
6. Note your **Site URL**: `https://your-domain.atlassian.net`
7. Note your **Email**

**Free Tier**: ✅ Up to 10 users
**Cost**: $0-70/month

---

## 📝 Configuration Template

Copy to `.env` file:

```bash
# Conviva
CONVIVA_ENABLED=true
CONVIVA_CUSTOMER_KEY=c3.your_company
CONVIVA_API_KEY=your_api_key_here

# NewRelic
NEWRELIC_ENABLED=true
NEWRELIC_API_KEY=NRAK-your_key_here
NEWRELIC_ACCOUNT_ID=1234567

# JIRA
JIRA_ENABLED=true
JIRA_FORCE_LIVE=true
JIRA_API_URL=https://your-domain.atlassian.net
JIRA_API_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_token_here
JIRA_PROJECT_KEY=PROD

# Confluence
CONFLUENCE_ENABLED=true
CONFLUENCE_API_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your_token_here
CONFLUENCE_SPACE_KEY=OPS
```

---

## 🚀 Quick Setup

```bash
# Interactive setup (recommended)
python scripts/setup_integrations.py

# Or manual setup
cp .env.example .env
nano .env  # Edit with your keys

# Test connections
python scripts/test_integrations.py --all

# Start server
python -m mcp.server
```

---

## ✅ Validation Checklist

- [ ] Conviva: Customer Key + API Key
- [ ] NewRelic: API Key (NRAK-) + Account ID
- [ ] JIRA: Site URL + Email + API Token
- [ ] Confluence: Same as JIRA + Space Key
- [ ] .env file created
- [ ] All connections tested
- [ ] Server starts successfully

---

## 🆘 Common Issues

### Conviva 401 Error
```
Problem: Unauthorized
Solution: Check Customer Key format (c3.company_name)
```

### NewRelic 403 Error
```
Problem: Forbidden
Solution: Ensure API key has query permissions
```

### JIRA Authentication Failed
```
Problem: Invalid credentials
Solution: Verify email and token, ensure no spaces
```

---

## 💡 Pro Tips

1. **Free Tier Options**:
   - NewRelic: 100GB/month free
   - Atlassian: 10 users free
   - Conviva: Request trial

2. **Security**:
   - Never commit `.env` to git
   - Use read-only API keys
   - Rotate keys quarterly

3. **Hybrid Mode** (Best for Demos):
   ```bash
   MOCK_MODE=true
   JIRA_FORCE_LIVE=true  # Only JIRA live
   ```

4. **Full Integration**:
   ```bash
   MOCK_MODE=false
   # Enable all services
   ```

---

## 📞 Support

- **Setup Script**: `python scripts/setup_integrations.py`
- **Test Script**: `python scripts/test_integrations.py --all`
- **Full Guide**: [INTEGRATION_SETUP.md](./INTEGRATION_SETUP.md)
- **Troubleshooting**: See setup guide

---

**Last Updated**: December 18, 2025

