"""
AI-powered intelligence layer for Paramount+ Media Operations.

Patent-worthy AI stack with zero external API dependencies:
- RAG pipeline for operational knowledge (ChromaDB + LangChain)
- Multi-agent systems for autonomous issue resolution (AutoGen/CrewAI)
- Computer vision for content intelligence (CLIP + YOLO)
- Voice AI for transcription and alerts (Whisper + TTS)
- Bayesian analytics for uncertainty quantification (PyMC)
- Advanced statistics (ARIMA, VAR, survival analysis)
- Workflow automation with state machines (LangGraph)
- NLP engine for text processing (spaCy + transformers)
- Anomaly detection for streaming metrics
- Predictive analytics for churn and revenue
- AI-generated insights and recommendations
"""

# Core AI modules (original)
from mcp.ai.anomaly_detector import AnomalyDetector, Anomaly
from mcp.ai.insights_generator import AIInsightsGenerator
from mcp.ai.predictive_analytics import PredictiveAnalytics

# Advanced AI modules (patent-worthy stack)
from mcp.ai.rag_engine import RAGEngine, get_rag_engine, RetrievalResult
from mcp.ai.multi_agent_system import (
    ProductionIssueResolver,
    get_issue_resolver,
    Agent,
    AgentRole,
    AgentAction,
    IssueResolutionPlan
)
from mcp.ai.vision_engine import (
    VisionEngine,
    get_vision_engine,
    ContentAnalysisResult,
    QualityIssue
)
from mcp.ai.voice_engine import (
    VoiceEngine,
    get_voice_engine,
    TranscriptionResult,
    AlertAudio
)
from mcp.ai.bayesian_analytics import (
    BayesianAnalytics,
    get_bayesian_analytics,
    BayesianPrediction,
    CausalImpactResult
)
from mcp.ai.advanced_statistics import (
    AdvancedStatistics,
    get_advanced_statistics,
    ForecastResult,
    CausalityResult,
    SurvivalAnalysisResult
)
from mcp.ai.workflow_automation import (
    ProductionWorkflow,
    get_production_workflow,
    WorkflowState,
    WorkflowContext
)
from mcp.ai.nlp_engine import (
    NLPEngine,
    get_nlp_engine,
    TextAnalysisResult,
    Entity
)

__all__ = [
    # Core modules
    "AnomalyDetector",
    "Anomaly",
    "AIInsightsGenerator",
    "PredictiveAnalytics",
    
    # RAG
    "RAGEngine",
    "get_rag_engine",
    "RetrievalResult",
    
    # Multi-agent
    "ProductionIssueResolver",
    "get_issue_resolver",
    "Agent",
    "AgentRole",
    "AgentAction",
    "IssueResolutionPlan",
    
    # Computer vision
    "VisionEngine",
    "get_vision_engine",
    "ContentAnalysisResult",
    "QualityIssue",
    
    # Voice AI
    "VoiceEngine",
    "get_voice_engine",
    "TranscriptionResult",
    "AlertAudio",
    
    # Bayesian analytics
    "BayesianAnalytics",
    "get_bayesian_analytics",
    "BayesianPrediction",
    "CausalImpactResult",
    
    # Advanced statistics
    "AdvancedStatistics",
    "get_advanced_statistics",
    "ForecastResult",
    "CausalityResult",
    "SurvivalAnalysisResult",
    
    # Workflow automation
    "ProductionWorkflow",
    "get_production_workflow",
    "WorkflowState",
    "WorkflowContext",
    
    # NLP
    "NLPEngine",
    "get_nlp_engine",
    "TextAnalysisResult",
    "Entity",
]
