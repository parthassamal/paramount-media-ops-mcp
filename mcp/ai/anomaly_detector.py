"""
AI-Powered Anomaly Detection Engine.

Detects anomalies in streaming metrics, production issues, and churn patterns
using statistical methods and machine learning.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from scipy import stats
import structlog

logger = structlog.get_logger()


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    
    metric_name: str
    timestamp: datetime
    actual_value: float
    expected_value: float
    deviation: float
    severity: str  # "low", "medium", "high", "critical"
    confidence: float
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp.isoformat(),
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "deviation": self.deviation,
            "severity": self.severity,
            "confidence": self.confidence,
            "context": self.context
        }


class AnomalyDetector:
    """
    Detects anomalies using multiple statistical methods.
    
    Methods:
    - Z-score detection for outliers
    - Interquartile Range (IQR) method
    - Moving average deviation
    - Time-series pattern recognition
    """
    
    def __init__(self, sensitivity: float = 0.95):
        """
        Initialize anomaly detector.
        
        Args:
            sensitivity: Detection sensitivity (0-1). Higher = more sensitive.
        """
        self.sensitivity = sensitivity
        self.z_threshold = self._calculate_z_threshold(sensitivity)
        
    def _calculate_z_threshold(self, sensitivity: float) -> float:
        """Calculate Z-score threshold from sensitivity."""
        # sensitivity 0.95 -> z=1.96, 0.99 -> z=2.58
        return stats.norm.ppf((1 + sensitivity) / 2)
    
    def detect_streaming_anomalies(
        self,
        metrics: List[Dict[str, Any]],
        metric_key: str = "buffering_ratio"
    ) -> List[Anomaly]:
        """
        Detect anomalies in streaming metrics.
        
        Args:
            metrics: List of streaming metrics with timestamps
            metric_key: Key to analyze (e.g., "buffering_ratio", "error_rate")
            
        Returns:
            List of detected anomalies
        """
        if len(metrics) < 10:
            logger.warning("Insufficient data for anomaly detection", count=len(metrics))
            return []
        
        # Extract values and timestamps
        values = np.array([m.get(metric_key, 0) for m in metrics])
        timestamps = [m.get("timestamp", datetime.now()) for m in metrics]
        
        anomalies = []
        
        # Method 1: Z-score detection
        z_anomalies = self._detect_zscore_anomalies(
            values, timestamps, metric_key, metrics
        )
        anomalies.extend(z_anomalies)
        
        # Method 2: IQR detection
        iqr_anomalies = self._detect_iqr_anomalies(
            values, timestamps, metric_key, metrics
        )
        anomalies.extend(iqr_anomalies)
        
        # Deduplicate and sort by severity
        anomalies = self._deduplicate_anomalies(anomalies)
        anomalies.sort(key=lambda a: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[a.severity],
            -a.confidence
        ), reverse=True)
        
        logger.info(
            "Streaming anomaly detection complete",
            metric=metric_key,
            anomalies_found=len(anomalies)
        )
        
        return anomalies
    
    def detect_churn_spikes(
        self,
        cohorts: List[Dict[str, Any]],
        lookback_days: int = 30
    ) -> List[Anomaly]:
        """
        Detect unusual spikes in churn rates.
        
        Args:
            cohorts: List of churn cohort data
            lookback_days: Days to look back for baseline
            
        Returns:
            List of detected churn anomalies
        """
        if not cohorts:
            return []
        
        # Extract churn rates over time
        churn_rates = np.array([
            c.get("churn_risk_score", 0) for c in cohorts
        ])
        
        # Calculate baseline statistics
        mean_churn = np.mean(churn_rates)
        std_churn = np.std(churn_rates)
        
        anomalies = []
        
        for i, cohort in enumerate(cohorts):
            churn_rate = cohort.get("churn_risk_score", 0)
            z_score = (churn_rate - mean_churn) / std_churn if std_churn > 0 else 0
            
            if abs(z_score) > self.z_threshold:
                severity = self._calculate_severity(abs(z_score))
                
                anomaly = Anomaly(
                    metric_name="churn_rate",
                    timestamp=datetime.now(),
                    actual_value=churn_rate,
                    expected_value=mean_churn,
                    deviation=abs(z_score),
                    severity=severity,
                    confidence=min(abs(z_score) / 4, 1.0),
                    context={
                        "cohort_id": cohort.get("cohort_id", f"COHORT-{i}"),
                        "cohort_name": cohort.get("name", "Unknown"),
                        "subscribers": cohort.get("subscribers", 0),
                        "primary_driver": cohort.get("primary_driver", "Unknown")
                    }
                )
                anomalies.append(anomaly)
        
        logger.info("Churn spike detection complete", anomalies_found=len(anomalies))
        return anomalies
    
    def detect_production_patterns(
        self,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns in production issues.
        
        Args:
            issues: List of production issues
            
        Returns:
            Insights about issue patterns
        """
        if not issues:
            return {"patterns": [], "insights": []}
        
        # Analyze severity distribution
        severity_counts = {}
        for issue in issues:
            severity = issue.get("severity", "Unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Detect unusual severity patterns
        total_issues = len(issues)
        critical_ratio = severity_counts.get("Critical", 0) / total_issues
        
        patterns = []
        insights = []
        
        # Pattern 1: High critical ratio
        if critical_ratio > 0.15:  # More than 15% critical
            patterns.append({
                "pattern": "high_critical_ratio",
                "description": f"{critical_ratio*100:.1f}% of issues are critical",
                "severity": "high",
                "recommendation": "Immediate escalation required"
            })
            insights.append(
                f"⚠️ Critical issue rate ({critical_ratio*100:.1f}%) is above normal threshold (15%)"
            )
        
        # Pattern 2: Recurring issue types
        issue_types = {}
        for issue in issues:
            issue_type = issue.get("type", "Unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Find dominant issue type
        if issue_types:
            dominant_type = max(issue_types.items(), key=lambda x: x[1])
            if dominant_type[1] / total_issues > 0.4:  # More than 40%
                patterns.append({
                    "pattern": "dominant_issue_type",
                    "description": f"{dominant_type[0]} accounts for {dominant_type[1]/total_issues*100:.1f}% of issues",
                    "severity": "medium",
                    "recommendation": f"Focus resources on {dominant_type[0]} resolution"
                })
                insights.append(
                    f"📊 {dominant_type[0]} is the dominant issue type ({dominant_type[1]} issues)"
                )
        
        # Pattern 3: Impact score distribution
        impact_scores = [issue.get("impact_score", 0) for issue in issues]
        if impact_scores:
            high_impact = sum(1 for score in impact_scores if score > 75)
            if high_impact / total_issues > 0.25:  # More than 25% high impact
                patterns.append({
                    "pattern": "high_impact_concentration",
                    "description": f"{high_impact} issues have high impact scores (>75)",
                    "severity": "high",
                    "recommendation": "Prioritize high-impact issues using Pareto analysis"
                })
                insights.append(
                    f"🎯 {high_impact} high-impact issues require immediate attention"
                )
        
        logger.info(
            "Production pattern detection complete",
            patterns_found=len(patterns),
            insights_generated=len(insights)
        )
        
        return {
            "patterns": patterns,
            "insights": insights,
            "severity_distribution": severity_counts,
            "issue_type_distribution": issue_types,
            "total_issues_analyzed": total_issues
        }
    
    def predict_incident_severity(
        self,
        issue: Dict[str, Any]
    ) -> Tuple[str, float]:
        """
        Predict incident severity based on features.
        
        Args:
            issue: Issue data
            
        Returns:
            Tuple of (predicted_severity, confidence)
        """
        # Simple rule-based prediction (can be replaced with ML model)
        score = 0
        factors = []
        
        # Factor 1: Affected users
        affected_users = issue.get("affected_users", 0)
        if affected_users > 10000:
            score += 40
            factors.append("high_user_impact")
        elif affected_users > 1000:
            score += 20
            factors.append("medium_user_impact")
        
        # Factor 2: Revenue impact
        revenue_impact = issue.get("estimated_revenue_impact", 0)
        if revenue_impact > 100000:
            score += 30
            factors.append("high_revenue_impact")
        elif revenue_impact > 10000:
            score += 15
            factors.append("medium_revenue_impact")
        
        # Factor 3: Issue type
        issue_type = issue.get("type", "").lower()
        if "critical" in issue_type or "outage" in issue_type:
            score += 20
            factors.append("critical_type")
        
        # Factor 4: Current severity
        current_severity = issue.get("severity", "Medium")
        if current_severity == "Critical":
            score += 10
            factors.append("already_critical")
        
        # Determine severity
        if score >= 70:
            severity = "Critical"
            confidence = 0.9
        elif score >= 50:
            severity = "High"
            confidence = 0.8
        elif score >= 30:
            severity = "Medium"
            confidence = 0.7
        else:
            severity = "Low"
            confidence = 0.6
        
        logger.debug(
            "Incident severity predicted",
            issue_id=issue.get("issue_id"),
            predicted_severity=severity,
            confidence=confidence,
            score=score,
            factors=factors
        )
        
        return severity, confidence
    
    def _detect_zscore_anomalies(
        self,
        values: np.ndarray,
        timestamps: List[datetime],
        metric_name: str,
        original_data: List[Dict[str, Any]]
    ) -> List[Anomaly]:
        """Detect anomalies using Z-score method."""
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return []
        
        z_scores = np.abs((values - mean) / std)
        anomalies = []
        
        for i, z_score in enumerate(z_scores):
            if z_score > self.z_threshold:
                severity = self._calculate_severity(z_score)
                
                anomaly = Anomaly(
                    metric_name=metric_name,
                    timestamp=timestamps[i] if i < len(timestamps) else datetime.now(),
                    actual_value=float(values[i]),
                    expected_value=float(mean),
                    deviation=float(z_score),
                    severity=severity,
                    confidence=min(z_score / 4, 1.0),
                    context={
                        "method": "zscore",
                        "threshold": self.z_threshold,
                        "data_point": original_data[i] if i < len(original_data) else {}
                    }
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_iqr_anomalies(
        self,
        values: np.ndarray,
        timestamps: List[datetime],
        metric_name: str,
        original_data: List[Dict[str, Any]]
    ) -> List[Anomaly]:
        """Detect anomalies using Interquartile Range method."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        if iqr == 0:
            return []
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        anomalies = []
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                deviation = abs(value - np.median(values)) / iqr
                severity = self._calculate_severity(deviation)
                
                anomaly = Anomaly(
                    metric_name=metric_name,
                    timestamp=timestamps[i] if i < len(timestamps) else datetime.now(),
                    actual_value=float(value),
                    expected_value=float(np.median(values)),
                    deviation=float(deviation),
                    severity=severity,
                    confidence=min(deviation / 3, 1.0),
                    context={
                        "method": "iqr",
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "data_point": original_data[i] if i < len(original_data) else {}
                    }
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_severity(self, deviation: float) -> str:
        """Calculate severity based on deviation magnitude."""
        if deviation >= 3.5:
            return "critical"
        elif deviation >= 2.5:
            return "high"
        elif deviation >= 1.5:
            return "medium"
        else:
            return "low"
    
    def _deduplicate_anomalies(self, anomalies: List[Anomaly]) -> List[Anomaly]:
        """Remove duplicate anomalies (same metric + timestamp)."""
        seen = set()
        unique = []
        
        for anomaly in anomalies:
            key = (anomaly.metric_name, anomaly.timestamp)
            if key not in seen:
                seen.add(key)
                unique.append(anomaly)
        
        return unique



