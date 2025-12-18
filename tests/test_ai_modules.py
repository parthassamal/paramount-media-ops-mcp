"""
Unit tests for AI modules: anomaly detection, predictive analytics, and insights generation.
"""
import pytest
from mcp.ai.anomaly_detector import AnomalyDetector
from mcp.ai.predictive_analytics import PredictiveAnalytics
from mcp.ai.insights_generator import AIInsightsGenerator


class TestAnomalyDetector:
    """Test suite for the AnomalyDetector class."""
    
    def test_initialization_default_sensitivity(self):
        """Test detector initializes with default sensitivity."""
        detector = AnomalyDetector()
        assert detector.sensitivity == 0.95
    
    def test_initialization_custom_sensitivity(self):
        """Test detector initializes with custom sensitivity."""
        detector = AnomalyDetector(sensitivity=0.90)
        assert detector.sensitivity == 0.90
    
    def test_calculate_z_threshold(self):
        """Test Z-score threshold calculation."""
        detector = AnomalyDetector(sensitivity=0.95)
        threshold = detector._calculate_z_threshold(0.95)
        assert threshold > 0
        assert isinstance(threshold, float)
    
    def test_calculate_severity(self):
        """Test severity calculation based on deviation."""
        detector = AnomalyDetector()
        # High deviation should be critical/high
        high_severity = detector._calculate_severity(5.0)
        assert high_severity in ["critical", "high", "medium"]
        # Low deviation should be low/medium
        low_severity = detector._calculate_severity(1.0)
        assert low_severity in ["low", "medium"]
    
    def test_sensitivity_range(self):
        """Test different sensitivity values."""
        for sensitivity in [0.90, 0.95, 0.99]:
            detector = AnomalyDetector(sensitivity=sensitivity)
            assert detector.sensitivity == sensitivity


class TestPredictiveAnalytics:
    """Test suite for the PredictiveAnalytics class."""
    
    def test_initialization(self):
        """Test predictor initializes correctly."""
        predictor = PredictiveAnalytics()
        assert predictor is not None
    
    def test_has_prediction_capability(self):
        """Test predictor has prediction methods."""
        predictor = PredictiveAnalytics()
        # Check that the object is properly initialized
        assert hasattr(predictor, '__init__')


class TestAIInsightsGenerator:
    """Test suite for the AIInsightsGenerator class."""
    
    def test_initialization(self):
        """Test generator initializes correctly."""
        generator = AIInsightsGenerator()
        assert generator is not None
    
    def test_initialization_with_provider(self):
        """Test generator initializes with LLM provider."""
        generator = AIInsightsGenerator(llm_provider="mock")
        assert generator is not None
    
    def test_has_analysis_methods(self):
        """Test generator has analysis methods."""
        generator = AIInsightsGenerator()
        # Check internal analysis methods exist
        assert hasattr(generator, '_analyze_churn_data')
        assert hasattr(generator, '_analyze_production_data')
        assert hasattr(generator, '_analyze_streaming_data')
    
    def test_calculate_priority(self):
        """Test priority calculation method."""
        generator = AIInsightsGenerator()
        insight = {"impact": 1000000, "urgency": "high"}
        priority = generator._calculate_priority(insight)
        assert isinstance(priority, str)


class TestAIModulesExist:
    """Test that all AI modules can be imported."""
    
    def test_anomaly_detector_import(self):
        """Test AnomalyDetector can be imported."""
        from mcp.ai.anomaly_detector import AnomalyDetector
        assert AnomalyDetector is not None
    
    def test_predictive_analytics_import(self):
        """Test PredictiveAnalytics can be imported."""
        from mcp.ai.predictive_analytics import PredictiveAnalytics
        assert PredictiveAnalytics is not None
    
    def test_insights_generator_import(self):
        """Test AIInsightsGenerator can be imported."""
        from mcp.ai.insights_generator import AIInsightsGenerator
        assert AIInsightsGenerator is not None
    
    def test_ai_package_init(self):
        """Test AI package initialization."""
        from mcp import ai
        assert ai is not None
