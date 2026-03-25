"""
Phase 2.5 — Cross-RCA Pattern Detection

Mines the SQLite RCA history for structural patterns:
- Temporal clusters (day/hour patterns)
- Deployment correlation
- Service co-failure pairs
- Recurring root causes (text similarity)
- MTTR trends per service
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
import sqlite3
from pathlib import Path

from mcp.db.rca_store import get_recent_rcas
from mcp.models.rca_models import PipelineStage
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

PATTERNS_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "rca_patterns.db"


@dataclass
class DetectedPattern:
    """A detected pattern across RCA history."""
    pattern_type: str
    affected_services: List[str]
    confidence_score: float
    incident_count: int
    description: str
    first_seen: datetime
    last_seen: datetime
    actionable_insight: str


class PatternDetector:
    """
    Detects patterns across RCA history that no single incident surfaces.
    
    Pattern types:
    - temporal_cluster: Time-of-day/week patterns
    - deployment_correlation: Incidents following deployments
    - service_co_failure: Services that fail together
    - recurring_root_cause: Similar AI summaries
    - mttr_trend: Increasing resolution time
    """
    
    def __init__(self):
        self.min_confidence = 0.7
        self.min_incidents = 3
        self._init_db()
    
    def _init_db(self):
        """Initialize patterns database."""
        PATTERNS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(PATTERNS_DB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                affected_services TEXT,
                confidence_score REAL,
                incident_count INTEGER,
                description TEXT,
                first_seen TEXT,
                last_seen TEXT,
                actionable_insight TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def detect_all(self) -> Dict[str, Any]:
        """
        Run all pattern detection algorithms.
        
        Returns:
            {
                "patterns": list,
                "summary": {
                    "total_patterns": int,
                    "by_type": dict,
                    "high_confidence": int
                },
                "analyzed_rcas": int
            }
        """
        logger.info("pattern_detection_started")
        
        # Get RCA history
        rcas = get_recent_rcas(limit=500)
        
        patterns = []
        
        # Detect each pattern type
        patterns.extend(self._detect_temporal_clusters(rcas))
        patterns.extend(self._detect_deployment_correlation(rcas))
        patterns.extend(self._detect_co_failures(rcas))
        patterns.extend(self._detect_recurring_root_causes(rcas))
        patterns.extend(self._detect_mttr_trends(rcas))
        
        # Filter by confidence and incident count
        patterns = [
            p for p in patterns
            if p.confidence_score >= self.min_confidence and p.incident_count >= self.min_incidents
        ]
        
        # Store patterns
        self._store_patterns(patterns)
        
        # Build summary
        by_type = defaultdict(int)
        for p in patterns:
            by_type[p.pattern_type] += 1
        
        result = {
            "patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "affected_services": p.affected_services,
                    "confidence_score": p.confidence_score,
                    "incident_count": p.incident_count,
                    "description": p.description,
                    "first_seen": p.first_seen.isoformat(),
                    "last_seen": p.last_seen.isoformat(),
                    "actionable_insight": p.actionable_insight
                }
                for p in patterns
            ],
            "summary": {
                "total_patterns": len(patterns),
                "by_type": dict(by_type),
                "high_confidence": len([p for p in patterns if p.confidence_score >= 0.85])
            },
            "analyzed_rcas": len(rcas)
        }
        
        logger.info(
            "pattern_detection_complete",
            total_patterns=len(patterns),
            analyzed=len(rcas)
        )
        
        return result
    
    def _detect_temporal_clusters(self, rcas) -> List[DetectedPattern]:
        """Detect time-of-day/week patterns."""
        patterns = []
        
        # Group by day-of-week and hour
        by_day_hour = defaultdict(list)
        for rca in rcas:
            dow = rca.created_at.strftime("%A")
            hour = rca.created_at.hour
            by_day_hour[(dow, hour)].append(rca)
        
        # Calculate baseline (average per slot)
        total = len(rcas)
        slots = 7 * 24
        baseline = total / slots if slots > 0 else 0
        
        for (dow, hour), rca_list in by_day_hour.items():
            count = len(rca_list)
            if count >= self.min_incidents and count > baseline * 2:
                # Get affected services
                services = list(set(r.service_name for r in rca_list if r.service_name))[:5]
                
                patterns.append(DetectedPattern(
                    pattern_type="temporal_cluster",
                    affected_services=services,
                    confidence_score=min(count / (baseline * 3), 1.0),
                    incident_count=count,
                    description=f"Incidents {count/baseline:.1f}x more likely on {dow} {hour:02d}:00-{hour+1:02d}:00",
                    first_seen=min(r.created_at for r in rca_list),
                    last_seen=max(r.created_at for r in rca_list),
                    actionable_insight=f"Schedule maintenance outside {dow} {hour:02d}:00"
                ))
        
        return patterns
    
    def _detect_deployment_correlation(self, rcas) -> List[DetectedPattern]:
        """Detect incidents correlated with deployments."""
        patterns = []
        
        # Group by service and check for temporal clustering
        by_service = defaultdict(list)
        for rca in rcas:
            if rca.service_name:
                by_service[rca.service_name].append(rca)
        
        for service, rca_list in by_service.items():
            if len(rca_list) < self.min_incidents:
                continue
            
            # Check if incidents cluster within 2-hour windows
            # (Would need deployment data for true correlation)
            time_diffs = []
            sorted_rcas = sorted(rca_list, key=lambda r: r.created_at)
            for i in range(1, len(sorted_rcas)):
                diff = (sorted_rcas[i].created_at - sorted_rcas[i-1].created_at).total_seconds() / 3600
                if diff < 4:  # Within 4 hours
                    time_diffs.append(diff)
            
            if len(time_diffs) >= 2:
                patterns.append(DetectedPattern(
                    pattern_type="deployment_correlation",
                    affected_services=[service],
                    confidence_score=min(len(time_diffs) / len(rca_list), 0.9),
                    incident_count=len(rca_list),
                    description=f"{service} incidents often occur in clusters",
                    first_seen=sorted_rcas[0].created_at,
                    last_seen=sorted_rcas[-1].created_at,
                    actionable_insight=f"Review deployment procedures for {service}"
                ))
        
        return patterns
    
    def _detect_co_failures(self, rcas) -> List[DetectedPattern]:
        """Detect service pairs that fail together."""
        patterns = []
        
        # Build co-occurrence matrix from impacted_components
        co_occur = defaultdict(int)
        service_count = defaultdict(int)
        
        for rca in rcas:
            components = rca.impacted_components or []
            if rca.service_name:
                components = [rca.service_name] + components
            
            components = list(set(components))[:10]  # Dedupe and limit
            
            for c in components:
                service_count[c] += 1
            
            for i, c1 in enumerate(components):
                for c2 in components[i+1:]:
                    pair = tuple(sorted([c1, c2]))
                    co_occur[pair] += 1
        
        # Find significant co-occurrences
        for (s1, s2), count in co_occur.items():
            if count >= self.min_incidents:
                # Calculate lift (co-occurrence vs expected)
                expected = (service_count[s1] * service_count[s2]) / len(rcas)
                lift = count / expected if expected > 0 else 0
                
                if lift > 2:  # Significant correlation
                    patterns.append(DetectedPattern(
                        pattern_type="service_co_failure",
                        affected_services=[s1, s2],
                        confidence_score=min(lift / 5, 1.0),
                        incident_count=count,
                        description=f"{s1} and {s2} co-fail {count} times (lift={lift:.1f}x)",
                        first_seen=datetime.utcnow() - timedelta(days=90),
                        last_seen=datetime.utcnow(),
                        actionable_insight=f"Check for shared dependency between {s1} and {s2}"
                    ))
        
        return patterns
    
    def _detect_recurring_root_causes(self, rcas) -> List[DetectedPattern]:
        """Detect similar root causes across RCAs."""
        patterns = []
        
        # Group by similar summaries using simple keyword matching
        # (In production, use sentence embeddings)
        keywords = defaultdict(list)
        
        for rca in rcas:
            if not rca.ai_summary:
                continue
            
            summary_lower = rca.ai_summary.lower()
            
            # Extract key phrases
            for phrase in ["cache", "timeout", "connection", "memory", "database", 
                          "authentication", "rate limit", "disk", "cpu", "network"]:
                if phrase in summary_lower:
                    keywords[phrase].append(rca)
        
        for phrase, rca_list in keywords.items():
            if len(rca_list) >= self.min_incidents:
                services = list(set(r.service_name for r in rca_list if r.service_name))[:5]
                
                patterns.append(DetectedPattern(
                    pattern_type="recurring_root_cause",
                    affected_services=services,
                    confidence_score=min(len(rca_list) / 10, 1.0),
                    incident_count=len(rca_list),
                    description=f"'{phrase}' appears in {len(rca_list)} RCA summaries",
                    first_seen=min(r.created_at for r in rca_list),
                    last_seen=max(r.created_at for r in rca_list),
                    actionable_insight=f"Create runbook for {phrase}-related incidents"
                ))
        
        return patterns
    
    def _detect_mttr_trends(self, rcas) -> List[DetectedPattern]:
        """Detect services with increasing MTTR."""
        patterns = []
        
        # Group completed RCAs by service with cycle time
        by_service = defaultdict(list)
        for rca in rcas:
            if rca.stage == PipelineStage.COMPLETED and rca.service_name:
                cycle_time = rca.cycle_time_hours
                if cycle_time:
                    by_service[rca.service_name].append({
                        "created_at": rca.created_at,
                        "cycle_time": cycle_time
                    })
        
        for service, data in by_service.items():
            if len(data) < 5:
                continue
            
            # Sort by date and split into halves
            sorted_data = sorted(data, key=lambda x: x["created_at"])
            mid = len(sorted_data) // 2
            
            first_half_avg = sum(d["cycle_time"] for d in sorted_data[:mid]) / mid
            second_half_avg = sum(d["cycle_time"] for d in sorted_data[mid:]) / (len(sorted_data) - mid)
            
            if second_half_avg > first_half_avg * 1.3:  # 30% increase
                increase_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                patterns.append(DetectedPattern(
                    pattern_type="mttr_trend",
                    affected_services=[service],
                    confidence_score=min(increase_pct / 100, 1.0),
                    incident_count=len(data),
                    description=f"{service} MTTR increased {increase_pct:.0f}% ({first_half_avg:.1f}h → {second_half_avg:.1f}h)",
                    first_seen=sorted_data[0]["created_at"],
                    last_seen=sorted_data[-1]["created_at"],
                    actionable_insight=f"Investigate why {service} incidents take longer to resolve"
                ))
        
        return patterns
    
    def _store_patterns(self, patterns: List[DetectedPattern]):
        """Store patterns in SQLite."""
        import json
        conn = sqlite3.connect(str(PATTERNS_DB_PATH))
        
        for p in patterns:
            pattern_id = f"{p.pattern_type}:{':'.join(p.affected_services[:3])}"
            conn.execute("""
                INSERT OR REPLACE INTO patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                p.pattern_type,
                json.dumps(p.affected_services),
                p.confidence_score,
                p.incident_count,
                p.description,
                p.first_seen.isoformat(),
                p.last_seen.isoformat(),
                p.actionable_insight,
                datetime.utcnow().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        service: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored patterns."""
        import json
        conn = sqlite3.connect(str(PATTERNS_DB_PATH))
        
        query = "SELECT * FROM patterns"
        params = []
        
        if pattern_type:
            query += " WHERE pattern_type = ?"
            params.append(pattern_type)
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        patterns = []
        for row in rows:
            affected = json.loads(row[2])
            if service and service not in affected:
                continue
            
            patterns.append({
                "pattern_id": row[0],
                "pattern_type": row[1],
                "affected_services": affected,
                "confidence_score": row[3],
                "incident_count": row[4],
                "description": row[5],
                "first_seen": row[6],
                "last_seen": row[7],
                "actionable_insight": row[8]
            })
        
        return patterns


# Singleton instance
pattern_detector = PatternDetector()


def detect_patterns() -> Dict[str, Any]:
    """Run pattern detection."""
    return pattern_detector.detect_all()


def get_patterns(
    pattern_type: Optional[str] = None,
    service: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get stored patterns."""
    return pattern_detector.get_patterns(pattern_type, service)
