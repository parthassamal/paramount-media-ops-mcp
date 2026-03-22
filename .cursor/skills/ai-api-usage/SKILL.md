---
name: ai-api-usage
description: Quick reference for using Paramount+ AI APIs. Use when testing AI endpoints, integrating AI features, or demonstrating AI capabilities.
---

# AI API Usage Skill

Quick reference and examples for all 25 AI API endpoints.

## When to Use

Use this skill when:
- Testing AI endpoints with curl or Postman
- Integrating AI features into other services
- Demonstrating AI capabilities
- Writing API integration code
- Debugging API responses

## Base URL

All AI endpoints are under: `http://localhost:8000/api/ai/`

## Quick Start Examples

### 1. RAG Semantic Search

Search operational knowledge base:
```bash
curl -X POST http://localhost:8000/api/ai/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to fix CDN buffering issues?",
    "top_k": 5,
    "source_type": "confluence"
  }'
```

**Response**:
```json
{
  "query": "How to fix CDN buffering issues?",
  "results": [
    {
      "content": "CDN buffering troubleshooting guide...",
      "source_type": "confluence",
      "metadata": {"page_id": "123", "title": "CDN Runbook"},
      "relevance_score": 0.89
    }
  ],
  "total_results": 5
}
```

### 2. Multi-Agent Issue Resolution

Autonomously resolve production issue:
```bash
curl -X POST http://localhost:8000/api/ai/agents/resolve-issue \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "PROD-789",
    "description": "15% buffering spike in EU-West region",
    "severity": "high",
    "metrics": {
      "buffering_rate": 0.15,
      "affected_users": 50000,
      "region": "eu-west"
    }
  }'
```

**Response**:
```json
{
  "issue_id": "PROD-789",
  "status": "resolved",
  "resolution_plan": {
    "root_cause": "CDN cache configuration",
    "recommended_actions": ["Flush CDN cache", "Update cache TTL"]
  },
  "agent_consensus_score": 0.92,
  "jira_ticket": "PROD-790",
  "actions_taken": [...]
}
```

### 3. Bayesian Churn Prediction

Predict churn with uncertainty:
```bash
curl -X POST http://localhost:8000/api/ai/bayesian/predict-churn \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "engagement_score": 0.25,
    "content_diversity": 0.30,
    "subscription_tenure_days": 60,
    "payment_issues": 2,
    "support_tickets": 4,
    "last_login_days_ago": 28
  }'
```

**Response**:
```json
{
  "user_id": "user-123",
  "churn_probability": 0.73,
  "credible_interval_95": [0.65, 0.81],
  "uncertainty": 0.08,
  "risk_category": "critical"
}
```

### 4. Voice Transcription

Transcribe support call:
```bash
curl -X POST http://localhost:8000/api/ai/voice/transcribe \
  -F "audio_file=@support_call.mp3"
```

**Response**:
```json
{
  "text": "I'm experiencing constant buffering...",
  "language": "en",
  "confidence": 0.94,
  "duration_seconds": 45.2,
  "complaint_keywords": ["buffering", "slow", "freezing"],
  "sentiment_score": -0.65,
  "sentiment_label": "negative"
}
```

### 5. Content Analysis

Analyze content thumbnail with CLIP:
```bash
curl -X POST http://localhost:8000/api/ai/vision/analyze-content \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "/path/to/thumbnail.jpg",
    "categories": ["action", "drama", "comedy", "sports"]
  }'
```

**Response**:
```json
{
  "predicted_category": "action",
  "confidence": 0.87,
  "all_scores": {
    "action": 0.87,
    "drama": 0.65,
    "comedy": 0.23,
    "sports": 0.12
  },
  "quality_score": 0.92,
  "quality_issues": []
}
```

### 6. Time-Series Forecasting

Forecast metrics using ARIMA or Prophet:
```bash
curl -X POST http://localhost:8000/api/ai/stats/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "time_series": [100, 105, 103, 108, 110, 115],
    "periods": 30,
    "method": "arima"
  }'
```

**Response**:
```json
{
  "forecast_values": [118, 120, 122, ...],
  "confidence_intervals": [[115, 121], [117, 123], ...],
  "forecast_dates": ["2026-02-01", "2026-02-02", ...],
  "model": "arima"
}
```

### 7. NLP Text Analysis

Comprehensive NLP analysis:
```bash
curl -X POST http://localhost:8000/api/ai/nlp/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The streaming quality for Yellowstone S5 has been excellent."
  }'
```

**Response**:
```json
{
  "text": "The streaming quality for Yellowstone S5 has been excellent.",
  "entities": [
    {"text": "Yellowstone S5", "label": "SHOW", "start_char": 28, "end_char": 42}
  ],
  "sentiment_score": 0.85,
  "sentiment_label": "positive",
  "keywords": ["streaming", "quality", "excellent", "yellowstone"],
  "language": "en"
}
```

## All Available Endpoints

### RAG (3 endpoints)
- `POST /api/ai/rag/search` - Semantic search
- `POST /api/ai/rag/query` - Question answering
- `GET /api/ai/rag/stats` - Knowledge base stats

### Multi-Agent (2 endpoints)
- `POST /api/ai/agents/resolve-issue` - Autonomous resolution
- `GET /api/ai/agents/performance` - Agent performance

### Computer Vision (3 endpoints)
- `POST /api/ai/vision/analyze-content` - Content categorization
- `POST /api/ai/vision/detect-quality-issues` - Quality check
- `POST /api/ai/vision/compare-similarity` - Image similarity

### Voice AI (2 endpoints)
- `POST /api/ai/voice/transcribe` - Audio transcription
- `POST /api/ai/voice/generate-alert` - TTS alerts

### Bayesian Analytics (2 endpoints)
- `POST /api/ai/bayesian/predict-churn` - Churn prediction
- `POST /api/ai/bayesian/causal-impact` - Causal analysis

### Advanced Statistics (2 endpoints)
- `POST /api/ai/stats/forecast` - Time-series forecast
- `POST /api/ai/stats/granger-causality` - Causality test

### Workflow Automation (2 endpoints)
- `POST /api/ai/workflow/execute` - Execute workflow
- `GET /api/ai/workflow/summary` - Workflow stats

### NLP (2 endpoints)
- `POST /api/ai/nlp/analyze` - Text analysis
- `POST /api/ai/nlp/summarize` - Text summarization

### Health Check (1 endpoint)
- `GET /api/ai/health` - Service health

## Interactive Documentation

View full API documentation with interactive testing:
```bash
open http://localhost:8000/docs
```

Navigate to **"AI Services"** section to see all endpoints with:
- Request/response schemas
- Try it out feature
- Example payloads
- Status code documentation

## Python Integration Example

```python
import httpx
import asyncio

class ParamountAIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def semantic_search(self, query: str, top_k: int = 5):
        response = await self.client.post(
            f"{self.base_url}/api/ai/rag/search",
            json={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()
    
    async def predict_churn(self, user_data: dict):
        response = await self.client.post(
            f"{self.base_url}/api/ai/bayesian/predict-churn",
            json=user_data
        )
        response.raise_for_status()
        return response.json()

# Usage
async def main():
    client = ParamountAIClient()
    results = await client.semantic_search("buffering issues")
    print(results)

asyncio.run(main())
```

## Performance Tips

- Use `top_k` parameter to limit results
- Cache frequent queries
- Use batch endpoints when available
- Monitor with `/health` endpoint
- Enable GPU for vision/voice models

## Documentation

- API Docs: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
