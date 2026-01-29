"""
FastAPI endpoints for advanced AI services.

Exposes all patent-worthy AI capabilities via REST API:
- RAG semantic search
- Multi-agent issue resolution
- Computer vision content analysis
- Voice transcription and alerts
- Bayesian churn prediction
- Advanced statistics and forecasting
- Workflow automation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import tempfile
import os

from mcp.ai import (
    get_rag_engine,
    get_issue_resolver,
    get_vision_engine,
    get_voice_engine,
    get_bayesian_analytics,
    get_advanced_statistics,
    get_production_workflow,
    get_nlp_engine
)
from mcp.utils.error_handler import (
    ServiceError,
    ValidationError as CustomValidationError,
    ModelNotFoundError,
    DataNotFoundError,
    retry_with_backoff
)
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/ai", tags=["AI Services"])


# =============================================================================
# Pydantic Models
# =============================================================================

class RAGSearchRequest(BaseModel):
    """Request for RAG semantic search."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    source_type: Optional[str] = Field(None, description="Filter by source type (confluence, jira, logs)")


class RAGSearchResponse(BaseModel):
    """Response for RAG semantic search."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int


class IssueResolutionRequest(BaseModel):
    """Request for autonomous issue resolution."""
    issue_id: str
    description: str
    severity: str = Field(default="medium", description="Issue severity (low, medium, high, critical)")
    metrics: Optional[Dict[str, Any]] = None


class IssueResolutionResponse(BaseModel):
    """Response for issue resolution."""
    issue_id: str
    status: str
    resolution_plan: Dict[str, Any]
    agent_consensus_score: float
    jira_ticket: str
    actions_taken: List[Dict[str, Any]]


class ContentAnalysisRequest(BaseModel):
    """Request for content thumbnail analysis."""
    image_url: str = Field(..., description="URL or path to image")
    categories: Optional[List[str]] = None


class ContentAnalysisResponse(BaseModel):
    """Response for content analysis."""
    predicted_category: str
    confidence: float
    all_scores: Dict[str, float]
    quality_score: float
    quality_issues: List[Dict[str, Any]]


class ChurnPredictionRequest(BaseModel):
    """Request for Bayesian churn prediction."""
    user_id: str
    engagement_score: float = Field(ge=0.0, le=1.0)
    content_diversity: float = Field(ge=0.0, le=1.0)
    subscription_tenure_days: int = Field(ge=0)
    payment_issues: int = Field(default=0, ge=0)
    support_tickets: int = Field(default=0, ge=0)
    last_login_days_ago: int = Field(default=7, ge=0)


class ChurnPredictionResponse(BaseModel):
    """Response for churn prediction."""
    user_id: str
    churn_probability: float
    credible_interval_95: tuple
    uncertainty: float
    risk_category: str


class ForecastRequest(BaseModel):
    """Request for time-series forecasting."""
    time_series: List[float] = Field(..., description="Historical time series data")
    periods: int = Field(default=30, ge=1, le=365, description="Number of periods to forecast")
    method: str = Field(default="arima", description="Forecasting method (arima, prophet)")


class ForecastResponse(BaseModel):
    """Response for forecasting."""
    forecast_values: List[float]
    confidence_intervals: List[tuple]
    forecast_dates: List[str]
    model: str


class WorkflowExecutionRequest(BaseModel):
    """Request for workflow execution."""
    issue_data: Dict[str, Any]


class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution."""
    issue_id: str
    final_state: str
    actions_taken: List[Dict[str, Any]]
    workflow_duration_seconds: float


class TextAnalysisRequest(BaseModel):
    """Request for NLP text analysis."""
    text: str = Field(..., description="Text to analyze")


class TextAnalysisResponse(BaseModel):
    """Response for text analysis."""
    text: str
    entities: List[Dict[str, Any]]
    sentiment_score: float
    sentiment_label: str
    keywords: List[str]
    language: str


# =============================================================================
# RAG Endpoints
# =============================================================================

@router.post("/rag/search", response_model=RAGSearchResponse)
@log_performance(operation="rag_semantic_search")
async def rag_semantic_search(request: RAGSearchRequest):
    """
    Semantic search across operational knowledge base (JIRA, Confluence, logs).
    
    Uses RAG with hybrid retrieval (dense + sparse) for finding relevant
    documentation, past issues, and operational context.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info("RAG search initiated", query=request.query[:100], top_k=request.top_k)
        
        rag_engine = get_rag_engine()
        
        results = rag_engine.semantic_search(
            query=request.query,
            top_k=request.top_k,
            source_type=request.source_type
        )
        
        formatted_results = [
            {
                "content": r.content,
                "source_type": r.source_type,
                "metadata": r.metadata,
                "relevance_score": r.score
            }
            for r in results
        ]
        
        logger.info("RAG search completed", result_count=len(formatted_results))
        
        return RAGSearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results)
        )
    
    except ModelNotFoundError as e:
        logger.error("RAG model not found", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service unavailable - model not loaded"
        )
    except DataNotFoundError as e:
        logger.warning("No data found for query", error=str(e))
        return RAGSearchResponse(query=request.query, results=[], total_results=0)
    except ValueError as e:
        logger.warning("Invalid input", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("RAG search failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during search"
        )


@router.post("/rag/query")
@log_performance(operation="rag_query")
async def rag_query_answer(query: str, top_k: int = 3):
    """
    Answer questions using RAG over indexed knowledge base.
    
    Retrieves relevant context and generates answer without external LLM.
    """
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty"
        )
    
    if top_k < 1 or top_k > 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="top_k must be between 1 and 20"
        )
    
    try:
        logger.info("RAG query initiated", query=query[:100])
        rag_engine = get_rag_engine()
        result = rag_engine.rag_query(query, top_k=top_k)
        logger.info("RAG query completed")
        return result
    except ModelNotFoundError as e:
        logger.error("RAG model not available", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service unavailable"
        )
    except Exception as e:
        logger.exception("RAG query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )


@router.get("/rag/stats")
@log_performance(operation="rag_stats")
async def rag_collection_stats():
    """Get statistics about indexed knowledge base."""
    try:
        logger.info("Fetching RAG collection stats")
        rag_engine = get_rag_engine()
        stats = rag_engine.get_collection_stats()
        return stats
    except ModelNotFoundError as e:
        logger.error("RAG engine not available", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service unavailable"
        )
    except Exception as e:
        logger.exception("Failed to get RAG stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# =============================================================================
# Multi-Agent Endpoints
# =============================================================================

@router.post("/agents/resolve-issue", response_model=IssueResolutionResponse)
@log_performance(operation="resolve_issue_autonomous")
@retry_with_backoff(max_retries=2, backoff_factor=1.5)
async def resolve_issue_autonomous(request: IssueResolutionRequest):
    """
    Autonomously resolve production issue using multi-agent collaboration.
    
    Agents (Analyzer, JIRA Specialist, Streaming Expert) collaborate to:
    - Diagnose root cause
    - Create JIRA ticket
    - Recommend fixes
    - Escalate if needed
    """
    if not request.issue_id or not request.description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="issue_id and description are required"
        )
    
    if request.severity not in ["low", "medium", "high", "critical"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="severity must be one of: low, medium, high, critical"
        )
    
    try:
        logger.info(
            "Multi-agent resolution initiated",
            issue_id=request.issue_id,
            severity=request.severity
        )
        
        resolver = get_issue_resolver()
        
        issue_data = {
            "id": request.issue_id,
            "description": request.description,
            "severity": request.severity,
            "metrics": request.metrics or {}
        }
        
        result = await resolver.resolve_issue_autonomous(issue_data)
        
        logger.info(
            "Issue resolution completed",
            issue_id=request.issue_id,
            status=result.get("status"),
            consensus=result.get("agent_consensus_score")
        )
        
        return IssueResolutionResponse(**result)
    
    except ModelNotFoundError as e:
        logger.error("Multi-agent system not available", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-agent service unavailable"
        )
    except ValueError as e:
        logger.warning("Invalid issue data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Issue resolution failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve issue"
        )


@router.get("/agents/performance")
async def get_agent_performance():
    """Get performance summary for all agents."""
    try:
        resolver = get_issue_resolver()
        summary = resolver.get_agent_performance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")


# =============================================================================
# Computer Vision Endpoints
# =============================================================================

@router.post("/vision/analyze-content", response_model=ContentAnalysisResponse)
async def analyze_content_thumbnail(request: ContentAnalysisRequest):
    """
    Analyze content thumbnail using CLIP for zero-shot classification.
    
    Categorizes content (action, drama, comedy, sports, etc.) and assesses quality
    without requiring training data.
    """
    try:
        vision_engine = get_vision_engine()
        
        result = vision_engine.analyze_content_thumbnail(
            image_path=request.image_url,
            categories=request.categories
        )
        
        return ContentAnalysisResponse(
            predicted_category=result.predicted_category,
            confidence=result.confidence,
            all_scores=result.all_scores,
            quality_score=result.quality_score,
            quality_issues=result.quality_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")


@router.post("/vision/detect-quality-issues")
async def detect_quality_issues(image_url: str):
    """Detect quality issues in content thumbnail."""
    try:
        vision_engine = get_vision_engine()
        issues = vision_engine.detect_quality_issues(image_url)
        
        return {
            "image_url": image_url,
            "quality_issues": [
                {
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    "description": issue.description
                }
                for issue in issues
            ],
            "total_issues": len(issues)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality detection failed: {str(e)}")


@router.post("/vision/compare-similarity")
async def compare_image_similarity(image_url_1: str, image_url_2: str):
    """Compare visual similarity between two images using CLIP embeddings."""
    try:
        vision_engine = get_vision_engine()
        similarity = vision_engine.compare_images_similarity(image_url_1, image_url_2)
        
        return {
            "image_1": image_url_1,
            "image_2": image_url_2,
            "similarity_score": similarity,
            "interpretation": "Very similar" if similarity > 0.8 else "Similar" if similarity > 0.6 else "Different"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity comparison failed: {str(e)}")


# =============================================================================
# Voice AI Endpoints
# =============================================================================

@router.post("/voice/transcribe")
@log_performance(operation="transcribe_audio")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe audio file using Whisper ASR.
    
    Extracts complaint keywords and analyzes sentiment.
    """
    # Validate file
    if not audio_file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No file provided"
        )
    
    # Check file extension
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm'}
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported audio format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Check file size (max 25MB)
    max_size = 25 * 1024 * 1024  # 25MB
    content = await audio_file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file too large (max 25MB)"
        )
    
    tmp_file_path = None
    try:
        logger.info(
            "Audio transcription initiated",
            filename=audio_file.filename,
            size_bytes=len(content)
        )
        
        voice_engine = get_voice_engine()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Transcribe
        result = voice_engine.transcribe_support_call(tmp_file_path)
        
        logger.info(
            "Transcription completed",
            text_length=len(result.text),
            language=result.language,
            confidence=result.confidence
        )
        
        return {
            "text": result.text,
            "language": result.language,
            "confidence": result.confidence,
            "duration_seconds": result.duration_seconds,
            "complaint_keywords": result.complaint_keywords,
            "sentiment_score": result.sentiment_score,
            "sentiment_label": "negative" if result.sentiment_score < -0.2 else "neutral" if result.sentiment_score < 0.2 else "positive"
        }
    
    except ModelNotFoundError as e:
        logger.error("Whisper model not available", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service unavailable - Whisper model not loaded"
        )
    except ValueError as e:
        logger.warning("Invalid audio file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid audio file: {str(e)}"
        )
    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )
    
    finally:
        # Clean up temp file
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning("Failed to cleanup temp file", path=tmp_file_path, error=str(e))


@router.post("/voice/generate-alert")
async def generate_voice_alert(alert_summary: str, severity: str = "high"):
    """
    Generate voice alert for critical production issue.
    
    Uses Coqui TTS to create audio notification.
    """
    try:
        voice_engine = get_voice_engine()
        
        alert_data = {
            "id": f"alert_{datetime.now().timestamp()}",
            "summary": alert_summary,
            "severity": severity,
            "action_required": "Please investigate immediately"
        }
        
        result = voice_engine.generate_alert_notification(alert_data, priority=severity)
        
        return {
            "audio_path": result.audio_path,
            "text": result.text,
            "duration_seconds": result.duration_seconds,
            "priority": result.priority
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert generation failed: {str(e)}")


# =============================================================================
# Bayesian Analytics Endpoints
# =============================================================================

@router.post("/bayesian/predict-churn", response_model=ChurnPredictionResponse)
async def predict_churn_bayesian(request: ChurnPredictionRequest):
    """
    Predict churn probability with Bayesian uncertainty quantification.
    
    Returns mean prediction with 95% credible intervals and uncertainty estimate.
    """
    try:
        bayesian = get_bayesian_analytics()
        
        user_data = {
            "engagement_score": request.engagement_score,
            "content_diversity": request.content_diversity,
            "subscription_tenure_days": request.subscription_tenure_days,
            "payment_issues": request.payment_issues,
            "support_tickets": request.support_tickets,
            "last_login_days_ago": request.last_login_days_ago
        }
        
        prediction = bayesian.bayesian_churn_prediction(user_data)
        
        # Determine risk category
        mean_prob = prediction.mean_prediction
        if mean_prob >= 0.7:
            risk_category = "critical"
        elif mean_prob >= 0.5:
            risk_category = "high"
        elif mean_prob >= 0.3:
            risk_category = "medium"
        else:
            risk_category = "low"
        
        return ChurnPredictionResponse(
            user_id=request.user_id,
            churn_probability=prediction.mean_prediction,
            credible_interval_95=prediction.credible_interval_95,
            uncertainty=prediction.uncertainty,
            risk_category=risk_category
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bayesian prediction failed: {str(e)}")


@router.post("/bayesian/causal-impact")
async def analyze_causal_impact(
    pre_intervention: List[float],
    post_intervention: List[float]
):
    """
    Analyze causal impact of an intervention (e.g., feature launch, bug fix).
    
    Uses Bayesian inference to estimate treatment effect with uncertainty.
    """
    try:
        bayesian = get_bayesian_analytics()
        
        result = bayesian.causal_impact_analysis(pre_intervention, post_intervention)
        
        return {
            "estimated_effect": result.estimated_effect,
            "credible_interval": result.credible_interval,
            "probability_positive_effect": result.probability_positive_effect,
            "is_significant": result.is_significant,
            "relative_effect_percent": result.relative_effect_percent,
            "interpretation": "Significant positive effect" if result.is_significant and result.estimated_effect > 0 
                            else "Significant negative effect" if result.is_significant and result.estimated_effect < 0
                            else "No significant effect"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Causal impact analysis failed: {str(e)}")


# =============================================================================
# Advanced Statistics Endpoints
# =============================================================================

@router.post("/stats/forecast", response_model=ForecastResponse)
async def forecast_time_series(request: ForecastRequest):
    """
    Forecast time series using ARIMA or Prophet.
    
    Returns forecast with confidence intervals.
    """
    try:
        stats = get_advanced_statistics()
        
        if request.method == "arima":
            result = stats.arima_forecast(request.time_series, periods=request.periods)
            
            return ForecastResponse(
                forecast_values=result.forecast_values,
                confidence_intervals=result.confidence_intervals,
                forecast_dates=result.forecast_dates,
                model="arima"
            )
        elif request.method == "prophet":
            # Prophet requires date format - generate synthetic dates
            from datetime import datetime, timedelta
            historical_data = [
                {"date": (datetime.now() - timedelta(days=len(request.time_series)-i)).strftime("%Y-%m-%d"), 
                 "revenue": value}
                for i, value in enumerate(request.time_series)
            ]
            
            result = stats.forecast_revenue_prophet(historical_data, forecast_months=request.periods // 30)
            
            return ForecastResponse(
                forecast_values=[f["yhat"] for f in result["forecast"][:request.periods]],
                confidence_intervals=[(f.get("yhat_lower", 0), f.get("yhat_upper", 0)) for f in result["forecast"][:request.periods]],
                forecast_dates=[f["ds"] for f in result["forecast"][:request.periods]],
                model="prophet"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@router.post("/stats/granger-causality")
async def test_granger_causality(
    churn_time_series: List[float],
    production_issues_time_series: List[float]
):
    """
    Test Granger causality: Do production issues cause churn?
    
    Uses VAR model to detect causal relationships.
    """
    try:
        stats = get_advanced_statistics()
        
        result = stats.multivariate_causality(
            churn_time_series,
            production_issues_time_series
        )
        
        return {
            "causality_detected": result.causality_detected,
            "p_value": result.p_value,
            "f_statistic": result.f_statistic,
            "conclusion": result.conclusion,
            "lag_order": result.lag_order,
            "interpretation": result.conclusion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Granger causality test failed: {str(e)}")


# =============================================================================
# Workflow Automation Endpoints
# =============================================================================

@router.post("/workflow/execute", response_model=WorkflowExecutionResponse)
async def execute_production_workflow(request: WorkflowExecutionRequest):
    """
    Execute automated workflow for production issue resolution.
    
    Uses LangGraph state machine to orchestrate:
    - Issue detection
    - Root cause analysis
    - JIRA ticket creation
    - Team notification
    - Resolution monitoring
    """
    try:
        workflow = get_production_workflow()
        result = await workflow.execute_workflow(request.issue_data)
        
        return WorkflowExecutionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/workflow/summary")
async def get_workflow_summary():
    """Get summary of workflow execution statistics."""
    try:
        workflow = get_production_workflow()
        summary = workflow.get_workflow_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow summary: {str(e)}")


# =============================================================================
# NLP Endpoints
# =============================================================================

@router.post("/nlp/analyze", response_model=TextAnalysisResponse)
async def analyze_text_nlp(request: TextAnalysisRequest):
    """
    Comprehensive NLP analysis using spaCy + transformers.
    
    Extracts entities, sentiment, keywords, and language.
    """
    try:
        nlp_engine = get_nlp_engine()
        result = nlp_engine.analyze_text(request.text)
        
        return TextAnalysisResponse(
            text=result.text,
            entities=[
                {
                    "text": e.text,
                    "label": e.label,
                    "start_char": e.start_char,
                    "end_char": e.end_char
                }
                for e in result.entities
            ],
            sentiment_score=result.sentiment_score,
            sentiment_label=result.sentiment_label,
            keywords=result.keywords,
            language=result.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP analysis failed: {str(e)}")


@router.post("/nlp/summarize")
async def summarize_text_nlp(text: str, max_sentences: int = 3):
    """Summarize text by extracting key sentences."""
    try:
        nlp_engine = get_nlp_engine()
        summary = nlp_engine.summarize_text(text, max_sentences=max_sentences)
        
        return {
            "original_text": text,
            "summary": summary,
            "compression_ratio": len(summary) / len(text) if len(text) > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def ai_services_health_check():
    """
    Health check for all AI services.
    
    Verifies that all AI engines are accessible.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check each service
    try:
        get_rag_engine()
        health_status["services"]["rag"] = "operational"
    except Exception as e:
        health_status["services"]["rag"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_issue_resolver()
        health_status["services"]["multi_agent"] = "operational"
    except Exception as e:
        health_status["services"]["multi_agent"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_vision_engine()
        health_status["services"]["computer_vision"] = "operational"
    except Exception as e:
        health_status["services"]["computer_vision"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_voice_engine()
        health_status["services"]["voice_ai"] = "operational"
    except Exception as e:
        health_status["services"]["voice_ai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_bayesian_analytics()
        health_status["services"]["bayesian_analytics"] = "operational"
    except Exception as e:
        health_status["services"]["bayesian_analytics"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_advanced_statistics()
        health_status["services"]["advanced_statistics"] = "operational"
    except Exception as e:
        health_status["services"]["advanced_statistics"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_production_workflow()
        health_status["services"]["workflow_automation"] = "operational"
    except Exception as e:
        health_status["services"]["workflow_automation"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        get_nlp_engine()
        health_status["services"]["nlp_engine"] = "operational"
    except Exception as e:
        health_status["services"]["nlp_engine"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
