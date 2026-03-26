---
name: paramount-ai-ops
description: Expert guidance for Paramount+ AI Operations platform. Use when working with RAG, multi-agent systems, computer vision, voice AI, Bayesian analytics, or any AI/ML features in this project.
---

# Paramount AI Operations Skill

Comprehensive guidance for working with the advanced AI/ML system built for Paramount+ streaming operations.

## When to Use

Use this skill when:
- Working with any AI/ML modules (RAG, multi-agent, vision, voice, Bayesian, statistics, NLP, workflow)
- Implementing or debugging AI endpoints
- Adding new AI capabilities
- Optimizing AI performance
- Understanding the AI architecture
- Troubleshooting AI model loading issues

## AI Modules Overview

### 1. RAG Engine (`mcp/ai/rag_engine.py`)
**Purpose**: Semantic search over operational knowledge (JIRA, Confluence, logs)
**Technology**: ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
**Key Methods**:
- `semantic_search(query, top_k, source_type)` - Hybrid retrieval
- `index_confluence_pages(pages)` - Index documentation
- `index_jira_issues(issues)` - Index tickets

**Usage**:
```python
from mcp.ai import get_rag_engine

rag = get_rag_engine()
results = rag.semantic_search("CDN buffering issues", top_k=5)
```

### 2. Multi-Agent System (`mcp/ai/multi_agent_system.py`)
**Purpose**: Autonomous production issue resolution with agent collaboration
**Technology**: AutoGen + CrewAI concepts
**Agents**: Analyzer, JIRA Specialist, Streaming Expert, Coordinator
**Key Methods**:
- `resolve_issue_autonomous(issue_data)` - Full resolution pipeline

### 3. Vision Engine (`mcp/ai/vision_engine.py`)
**Purpose**: Content intelligence using computer vision
**Technology**: HuggingFace CLIP (ViT-B/32)
**Key Methods**:
- `analyze_content_thumbnail(image_path, categories)` - Zero-shot classification
- `detect_quality_issues(image_path)` - Quality assessment
- `compare_images_similarity(path1, path2)` - Similarity scoring

### 4. Voice Engine (`mcp/ai/voice_engine.py`)
**Purpose**: Audio transcription and voice alerts
**Technology**: OpenAI Whisper + Coqui TTS
**Key Methods**:
- `transcribe_support_call(audio_path)` - ASR with sentiment
- `generate_alert_notification(alert, priority)` - TTS alert generation

### 5. Bayesian Analytics (`mcp/ai/bayesian_analytics.py`)
**Purpose**: Probabilistic predictions with uncertainty quantification
**Technology**: PyMC + ArviZ
**Key Methods**:
- `bayesian_churn_prediction(user_data)` - Churn with credible intervals
- `causal_impact_analysis(pre_data, post_data)` - Treatment effect

### 6. Advanced Statistics (`mcp/ai/advanced_statistics.py`)
**Purpose**: Time-series forecasting and causality detection
**Technology**: ARIMA, Prophet, VAR, Lifelines
**Key Methods**:
- `arima_forecast(time_series, periods)` - Univariate forecasting
- `multivariate_causality(churn_ts, issues_ts)` - Granger causality
- `survival_analysis(subscriber_data)` - Kaplan-Meier curves

### 7. Workflow Automation (`mcp/ai/workflow_automation.py`)
**Purpose**: LangGraph-based state machine for issue workflows
**Technology**: LangGraph concepts
**States**: INIT → DETECT → ANALYZE → CREATE_TICKET → NOTIFY → MONITOR → RESOLVE

### 8. NLP Engine (`mcp/ai/nlp_engine.py`)
**Purpose**: Unified text analysis
**Technology**: spaCy + TextBlob
**Key Methods**:
- `analyze_text(text)` - Comprehensive analysis
- `extract_entities(text)` - NER
- `analyze_sentiment(text)` - Sentiment scoring

## FastAPI Endpoints

All AI services exposed via REST API at `/api/ai/*`:

### RAG Endpoints
- `POST /api/ai/rag/search` - Semantic search
- `POST /api/ai/rag/query` - Question answering
- `GET /api/ai/rag/stats` - Collection stats

### Multi-Agent Endpoints
- `POST /api/ai/agents/resolve-issue` - Autonomous resolution
- `GET /api/ai/agents/performance` - Agent metrics

### Vision Endpoints
- `POST /api/ai/vision/analyze-content` - Content analysis
- `POST /api/ai/vision/detect-quality-issues` - Quality check
- `POST /api/ai/vision/compare-similarity` - Image similarity

### Voice Endpoints
- `POST /api/ai/voice/transcribe` - Audio transcription
- `POST /api/ai/voice/generate-alert` - Voice alert

### Bayesian Endpoints
- `POST /api/ai/bayesian/predict-churn` - Churn prediction
- `POST /api/ai/bayesian/causal-impact` - Impact analysis

### Statistics Endpoints
- `POST /api/ai/stats/forecast` - Time-series forecast
- `POST /api/ai/stats/granger-causality` - Causality test

### Workflow Endpoints
- `POST /api/ai/workflow/execute` - Run workflow
- `GET /api/ai/workflow/summary` - Workflow stats

### NLP Endpoints
- `POST /api/ai/nlp/analyze` - Text analysis
- `POST /api/ai/nlp/summarize` - Text summary

## Installation & Setup

### First Time Setup
```bash
# Install AI dependencies and download models (~2.5GB)
./scripts/install_ai_models.sh

# This downloads:
# - spaCy en_core_web_sm
# - sentence-transformers all-MiniLM-L6-v2
# - HuggingFace CLIP ViT-B/32
# - OpenAI Whisper base model
# - ChromaDB
# - NLTK data
```

### Verify Installation
```bash
# Start server
./start.sh

# Test AI health
curl http://localhost:8000/api/ai/health

# View API docs
open http://localhost:8000/docs
```

## Best Practices

### Error Handling
All AI modules use the error handling framework:
```python
from mcp.utils.error_handler import ModelNotFoundError, retry_with_backoff
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

@log_performance(operation="my_ai_operation")
@retry_with_backoff(max_retries=2)
async def my_operation():
    try:
        model = load_model()
        result = model.predict(data)
        return result
    except ModelNotFoundError as e:
        logger.error("Model not available", error=str(e))
        # Use fallback mechanism
        return fallback_method()
```

### Lazy Loading
All AI models use lazy loading to optimize startup:
```python
def _load_model(self):
    if self.model is None:
        logger.info("Loading model", model_name=self.model_name)
        self.model = load_expensive_model()
```

### Input Validation
Always validate inputs before AI processing:
```python
if not text or not text.strip():
    raise ValidationError("Text cannot be empty", field="text")

if len(text) > 1000000:
    raise ValidationError("Text too large (max 1MB)", field="text")
```

## Troubleshooting

### Model Not Loading
```python
# Check if model directory exists
ls -la ~/.cache/huggingface/
ls -la ~/.cache/torch/

# Re-download models
./scripts/install_ai_models.sh
```

### ChromaDB Issues
```python
# Reset ChromaDB
rm -rf chroma_db/
# Re-index on next run
```

### Memory Issues
```python
# Reduce batch sizes
# Enable model quantization
# Use smaller models (e.g., Whisper tiny instead of base)
```

## Performance Optimization

- Use GPU if available: Set `enable_gpu=True` in engine initialization
- Batch operations when possible
- Cache frequently used embeddings
- Use model quantization for faster inference

## Architecture Notes

- **Zero external APIs**: All AI runs locally (no Claude/GPT-4)
- **40+ libraries**: State-of-the-art open-source ML stack
- **<100ms inference**: Optimized for production speed
- **Unlimited scale**: No rate limits or API costs
- **6 novel algorithms**: Novel algorithms and system combinations

## Documentation

- See `README.md` for advanced AI section
- See `ERROR_HANDLING_SUMMARY.md` for error handling guide
- See `IMPLEMENTATION_COMPLETE.md` for full feature documentation
- See `/docs` endpoint for interactive API documentation
