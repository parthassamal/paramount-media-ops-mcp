"""
Comprehensive unit tests for AI modules to achieve higher coverage.
"""
import pytest
import numpy as np
from mcp.ai.anomaly_detector import AnomalyDetector, Anomaly
from mcp.ai.predictive_analytics import PredictiveAnalytics
from mcp.ai.insights_generator import AIInsightsGenerator
from datetime import datetime


class TestAnomalyDetectorComprehensive:
    """Comprehensive tests for AnomalyDetector."""
    
    def test_anomaly_dataclass(self):
        """Test Anomaly dataclass creation and conversion."""
        anomaly = Anomaly(
            metric_name="buffering_ratio",
            timestamp=datetime.now(),
            actual_value=15.0,
            expected_value=2.5,
            deviation=5.0,
            severity="high",
            confidence=0.95,
            context={"region": "US"}
        )
        
        # Test to_dict conversion
        anomaly_dict = anomaly.to_dict()
        assert anomaly_dict["metric_name"] == "buffering_ratio"
        assert anomaly_dict["actual_value"] == 15.0
        assert anomaly_dict["severity"] == "high"
        assert isinstance(anomaly_dict["timestamp"], str)
    
    def test_calculate_z_threshold_various_sensitivities(self):
        """Test Z-threshold calculation for various sensitivities."""
        detector = AnomalyDetector()
        
        # Higher sensitivity = higher threshold
        t_90 = detector._calculate_z_threshold(0.90)
        t_95 = detector._calculate_z_threshold(0.95)
        t_99 = detector._calculate_z_threshold(0.99)
        
        assert t_90 < t_95 < t_99
        assert all(t > 0 for t in [t_90, t_95, t_99])
    
    def test_calculate_severity_thresholds(self):
        """Test severity calculation at various deviation levels."""
        detector = AnomalyDetector()
        
        # Test boundary conditions
        severities = [
            detector._calculate_severity(0.5),
            detector._calculate_severity(2.0),
            detector._calculate_severity(3.0),
            detector._calculate_severity(4.0),
            detector._calculate_severity(6.0),
        ]
        
        # Each should return a valid severity string
        valid_severities = ["low", "medium", "high", "critical"]
        for sev in severities:
            assert sev in valid_severities


class TestPredictiveAnalyticsComprehensive:
    """Comprehensive tests for PredictiveAnalytics."""
    
    def test_initialization_creates_instance(self):
        """Test that initialization works."""
        predictor = PredictiveAnalytics()
        assert predictor is not None
    
    def test_multiple_instances_independent(self):
        """Test multiple instances are independent."""
        p1 = PredictiveAnalytics()
        p2 = PredictiveAnalytics()
        assert p1 is not p2


class TestAIInsightsGeneratorComprehensive:
    """Comprehensive tests for AIInsightsGenerator."""
    
    def test_initialization_with_different_providers(self):
        """Test initialization with different LLM providers."""
        # Default provider
        g1 = AIInsightsGenerator()
        assert g1 is not None
        
        # Mock provider
        g2 = AIInsightsGenerator(llm_provider="mock")
        assert g2 is not None
        
        # Invalid provider (should still work)
        g3 = AIInsightsGenerator(llm_provider="invalid")
        assert g3 is not None
    
    def test_internal_analysis_methods_exist(self):
        """Test that internal analysis methods exist and are callable."""
        generator = AIInsightsGenerator()
        
        # Test churn data analysis
        churn_result = generator._analyze_churn_data({
            "at_risk_count": 100000,
            "revenue_impact": 5000000
        })
        assert isinstance(churn_result, dict)
        
        # Test production data analysis
        prod_result = generator._analyze_production_data({
            "critical_issues": 5,
            "total_delay_days": 50
        })
        assert isinstance(prod_result, dict)
        
        # Test streaming data analysis
        streaming_result = generator._analyze_streaming_data({
            "buffering_ratio": 3.5,
            "error_rate": 0.02
        })
        assert isinstance(streaming_result, dict)
    
    def test_calculate_priority_various_inputs(self):
        """Test priority calculation with various inputs."""
        generator = AIInsightsGenerator()
        
        # High impact, high urgency
        p1 = generator._calculate_priority({
            "impact": 10000000,
            "urgency": "critical"
        })
        
        # Low impact
        p2 = generator._calculate_priority({
            "impact": 1000
        })
        
        # Empty input
        p3 = generator._calculate_priority({})
        
        assert all(isinstance(p, str) for p in [p1, p2, p3])
    
    def test_generator_has_required_methods(self):
        """Test generator has all required internal methods."""
        generator = AIInsightsGenerator()
        
        # Check internal methods exist
        assert hasattr(generator, '_generate_priority_recommendation')
        assert hasattr(generator, '_analyze_churn_data')
        assert hasattr(generator, '_analyze_production_data')
        assert hasattr(generator, '_analyze_streaming_data')
        assert hasattr(generator, '_calculate_priority')
        
        # All should be callable
        assert callable(generator._generate_priority_recommendation)
        assert callable(generator._analyze_churn_data)


class TestAIModulesEdgeCases:
    """Test edge cases across all AI modules."""
    
    def test_anomaly_detector_with_empty_context(self):
        """Test Anomaly with empty context."""
        anomaly = Anomaly(
            metric_name="test",
            timestamp=datetime.now(),
            actual_value=1.0,
            expected_value=0.5,
            deviation=2.0,
            severity="low",
            confidence=0.8,
            context={}
        )
        result = anomaly.to_dict()
        assert result["context"] == {}
    
    def test_anomaly_detector_sensitivities(self):
        """Test various sensitivity levels."""
        for sens in [0.80, 0.85, 0.90, 0.95, 0.99]:
            detector = AnomalyDetector(sensitivity=sens)
            assert detector.sensitivity == sens
    
    def test_insights_generator_empty_data(self):
        """Test insights generator with empty data."""
        generator = AIInsightsGenerator()
        
        # Empty churn data
        result1 = generator._analyze_churn_data({})
        assert isinstance(result1, dict)
        
        # Empty production data
        result2 = generator._analyze_production_data({})
        assert isinstance(result2, dict)
        
        # Empty streaming data
        result3 = generator._analyze_streaming_data({})
        assert isinstance(result3, dict)


class TestAIPackageStructure:
    """Test AI package structure and imports."""
    
    def test_all_modules_importable(self):
        """Test all AI modules can be imported."""
        from mcp.ai import anomaly_detector
        from mcp.ai import predictive_analytics
        from mcp.ai import insights_generator
        
        assert anomaly_detector is not None
        assert predictive_analytics is not None
        assert insights_generator is not None
    
    def test_classes_have_docstrings(self):
        """Test main classes have documentation."""
        assert AnomalyDetector.__doc__ is not None
        assert PredictiveAnalytics.__doc__ is not None
        assert AIInsightsGenerator.__doc__ is not None

