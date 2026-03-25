"""
Phase 2.7 — Test Effectiveness Scoring

Track how often a test case:
- Detects real regressions (true positives)
- Fails without a corresponding production incident (false positives)
- Passes despite a production incident in its refs (missed detection)

Builds a per-case effectiveness score over time.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import sqlite3
from pathlib import Path

from mcp.tools.testrail_tool import get_all_cases, get_results_for_case, _tr
from mcp.db.rca_store import get_recent_rcas
from mcp.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)

EFFECTIVENESS_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "test_effectiveness.db"


@dataclass
class EffectivenessScore:
    """Effectiveness score for a single test case."""
    case_id: int
    title: str
    true_positives: int     # Failures that caught real bugs
    false_positives: int    # Failures with no corresponding incident
    missed_detections: int  # Passes during incidents in its scope
    total_runs: int
    effectiveness_score: float  # 0-100
    recommendation: str


class TestEffectivenessTracker:
    """
    Tracks test effectiveness over time.
    
    Metrics:
    - Precision: TP / (TP + FP)
    - Recall: TP / (TP + Missed)
    - F1: Harmonic mean
    - Effectiveness: Weighted score 0-100
    """
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize effectiveness database."""
        EFFECTIVENESS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(EFFECTIVENESS_DB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_metrics (
                case_id INTEGER PRIMARY KEY,
                title TEXT,
                true_positives INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                missed_detections INTEGER DEFAULT 0,
                total_runs INTEGER DEFAULT 0,
                effectiveness_score REAL DEFAULT 50.0,
                last_updated TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incident_correlations (
                correlation_id TEXT PRIMARY KEY,
                case_id INTEGER,
                run_id INTEGER,
                rca_id TEXT,
                correlation_type TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def calculate_scores(
        self,
        suite_id: Optional[int] = None,
        recalculate: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate effectiveness scores for all test cases.
        
        Args:
            suite_id: Suite to analyze (default: all)
            recalculate: Force recalculation even if cached
            
        Returns:
            {
                "total_cases": int,
                "average_effectiveness": float,
                "top_performers": list,
                "underperformers": list,
                "recommendations": list
            }
        """
        logger.info("effectiveness_calculation_started")
        
        # Get all cases
        cases = get_all_cases(suite_id)
        
        # Get RCA history for correlation
        rca_history = self._build_rca_map()
        
        # Calculate for each case
        scores = []
        for case in cases:
            score = self._calculate_case_score(case, rca_history)
            if score:
                scores.append(score)
                self._store_score(score)
        
        # Sort by effectiveness
        scores.sort(key=lambda s: s.effectiveness_score, reverse=True)
        
        # Build recommendations
        recommendations = self._generate_recommendations(scores)
        
        avg_score = sum(s.effectiveness_score for s in scores) / len(scores) if scores else 50
        
        result = {
            "total_cases": len(scores),
            "average_effectiveness": round(avg_score, 1),
            "top_performers": [
                {
                    "case_id": s.case_id,
                    "title": s.title,
                    "effectiveness_score": round(s.effectiveness_score, 1),
                    "true_positives": s.true_positives,
                    "total_runs": s.total_runs
                }
                for s in scores[:10]
            ],
            "underperformers": [
                {
                    "case_id": s.case_id,
                    "title": s.title,
                    "effectiveness_score": round(s.effectiveness_score, 1),
                    "false_positives": s.false_positives,
                    "missed_detections": s.missed_detections,
                    "recommendation": s.recommendation
                }
                for s in scores[-10:] if s.effectiveness_score < 50
            ],
            "recommendations": recommendations
        }
        
        logger.info(
            "effectiveness_calculation_complete",
            total=len(scores),
            avg_score=avg_score
        )
        
        return result
    
    def get_case_details(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed effectiveness metrics for a single case."""
        conn = sqlite3.connect(str(EFFECTIVENESS_DB_PATH))
        row = conn.execute(
            "SELECT * FROM case_metrics WHERE case_id = ?",
            (case_id,)
        ).fetchone()
        conn.close()
        
        if not row:
            return None
        
        total = row[3] + row[4] + row[5]
        precision = row[3] / (row[3] + row[4]) if (row[3] + row[4]) > 0 else 0
        recall = row[3] / (row[3] + row[5]) if (row[3] + row[5]) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "case_id": row[0],
            "title": row[1],
            "true_positives": row[2],
            "false_positives": row[3],
            "missed_detections": row[4],
            "total_runs": row[5],
            "effectiveness_score": row[6],
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1, 2),
            "last_updated": row[7]
        }
    
    def record_correlation(
        self,
        case_id: int,
        run_id: int,
        rca_id: str,
        correlation_type: str  # true_positive, false_positive, missed
    ):
        """Record a correlation between a test result and incident."""
        conn = sqlite3.connect(str(EFFECTIVENESS_DB_PATH))
        
        correlation_id = f"{case_id}-{run_id}-{rca_id}"
        
        conn.execute(
            "INSERT OR REPLACE INTO incident_correlations VALUES (?, ?, ?, ?, ?, ?)",
            (correlation_id, case_id, run_id, rca_id, correlation_type, 
             datetime.utcnow().isoformat())
        )
        
        # Update case metrics
        if correlation_type == "true_positive":
            conn.execute(
                "UPDATE case_metrics SET true_positives = true_positives + 1, last_updated = ? WHERE case_id = ?",
                (datetime.utcnow().isoformat(), case_id)
            )
        elif correlation_type == "false_positive":
            conn.execute(
                "UPDATE case_metrics SET false_positives = false_positives + 1, last_updated = ? WHERE case_id = ?",
                (datetime.utcnow().isoformat(), case_id)
            )
        elif correlation_type == "missed":
            conn.execute(
                "UPDATE case_metrics SET missed_detections = missed_detections + 1, last_updated = ? WHERE case_id = ?",
                (datetime.utcnow().isoformat(), case_id)
            )
        
        conn.commit()
        conn.close()
        
        logger.info(
            "correlation_recorded",
            case_id=case_id,
            correlation_type=correlation_type
        )
    
    def get_trends(
        self,
        case_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get effectiveness trends over time."""
        conn = sqlite3.connect(str(EFFECTIVENESS_DB_PATH))
        
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT correlation_type, COUNT(*) 
            FROM incident_correlations 
            WHERE created_at > ?
        """
        params = [cutoff]
        
        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)
        
        query += " GROUP BY correlation_type"
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        counts = {row[0]: row[1] for row in rows}
        
        tp = counts.get("true_positive", 0)
        fp = counts.get("false_positive", 0)
        missed = counts.get("missed", 0)
        
        total = tp + fp + missed
        
        return {
            "period_days": days,
            "case_id": case_id,
            "true_positives": tp,
            "false_positives": fp,
            "missed_detections": missed,
            "total_correlations": total,
            "precision": round(tp / (tp + fp), 2) if (tp + fp) > 0 else None,
            "recall": round(tp / (tp + missed), 2) if (tp + missed) > 0 else None
        }
    
    def _calculate_case_score(
        self,
        case: Dict[str, Any],
        rca_history: Dict[str, List]
    ) -> Optional[EffectivenessScore]:
        """Calculate effectiveness score for a single case."""
        case_id = case["id"]
        title = case.get("title", "")
        refs = case.get("refs") or ""
        
        # Get test results
        try:
            results = get_results_for_case(case_id, limit=50)
        except Exception:
            results = []
        
        if not results:
            return None
        
        # Count outcomes
        total_runs = len(results)
        failures = [r for r in results if r.get("status_id") == 5]
        passes = [r for r in results if r.get("status_id") == 1]
        
        # Correlate with RCAs
        true_positives = 0
        false_positives = 0
        missed_detections = 0
        
        # Get RCAs for this service/refs
        relevant_rcas = rca_history.get(refs.lower(), [])
        relevant_rcas += rca_history.get(title.lower()[:20], [])
        relevant_rcas = list(set(relevant_rcas))  # Dedupe
        
        for failure in failures:
            run_time = failure.get("created_on")
            if run_time:
                fail_time = datetime.fromtimestamp(run_time)
                # Check if RCA exists within 24 hours
                nearby_rca = any(
                    abs((rca_time - fail_time).total_seconds()) < 86400
                    for rca_time in relevant_rcas
                )
                if nearby_rca:
                    true_positives += 1
                else:
                    false_positives += 1
        
        for passing in passes:
            run_time = passing.get("created_on")
            if run_time:
                pass_time = datetime.fromtimestamp(run_time)
                # Check if test passed during an incident
                missed = any(
                    abs((rca_time - pass_time).total_seconds()) < 86400
                    for rca_time in relevant_rcas
                )
                if missed:
                    missed_detections += 1
        
        # Calculate score (weighted F1-like)
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.5
        recall = true_positives / (true_positives + missed_detections) if (true_positives + missed_detections) > 0 else 0.5
        
        # Effectiveness is weighted: precision matters more (we want low false positives)
        score = (precision * 0.6 + recall * 0.4) * 100
        
        # Determine recommendation
        if false_positives > true_positives and false_positives > 5:
            recommendation = "High false positive rate - investigate test stability"
        elif missed_detections > true_positives and missed_detections > 3:
            recommendation = "Low detection rate - strengthen assertions"
        elif score < 30:
            recommendation = "Consider retiring or reworking this test"
        elif score > 80:
            recommendation = "High-value test - ensure maintained"
        else:
            recommendation = "Normal performance"
        
        return EffectivenessScore(
            case_id=case_id,
            title=title,
            true_positives=true_positives,
            false_positives=false_positives,
            missed_detections=missed_detections,
            total_runs=total_runs,
            effectiveness_score=score,
            recommendation=recommendation
        )
    
    def _build_rca_map(self) -> Dict[str, List[datetime]]:
        """Build map of services/tickets to RCA timestamps."""
        rca_map = {}
        
        try:
            rcas = get_recent_rcas(limit=200)
            for rca in rcas:
                keys = []
                if rca.service_name:
                    keys.append(rca.service_name.lower())
                if rca.jira_ticket_id:
                    keys.append(rca.jira_ticket_id.lower())
                
                for key in keys:
                    if key not in rca_map:
                        rca_map[key] = []
                    rca_map[key].append(rca.created_at)
        except Exception:
            pass
        
        return rca_map
    
    def _store_score(self, score: EffectivenessScore):
        """Store score in database."""
        conn = sqlite3.connect(str(EFFECTIVENESS_DB_PATH))
        conn.execute("""
            INSERT OR REPLACE INTO case_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score.case_id,
            score.title,
            score.true_positives,
            score.false_positives,
            score.missed_detections,
            score.total_runs,
            score.effectiveness_score,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _generate_recommendations(self, scores: List[EffectivenessScore]) -> List[str]:
        """Generate suite-level recommendations."""
        recommendations = []
        
        # Count issues
        high_fp = len([s for s in scores if s.false_positives > 5])
        low_detect = len([s for s in scores if s.missed_detections > 3])
        underperf = len([s for s in scores if s.effectiveness_score < 30])
        
        if high_fp > len(scores) * 0.1:
            recommendations.append(
                f"{high_fp} tests ({high_fp/len(scores)*100:.0f}%) have high false positive rates - "
                "consider flaky test quarantine"
            )
        
        if low_detect > len(scores) * 0.05:
            recommendations.append(
                f"{low_detect} tests may have weak assertions - "
                "review test specifications against production incidents"
            )
        
        if underperf > 10:
            recommendations.append(
                f"{underperf} tests score below 30% - "
                "prioritize for retirement or rework in suite hygiene"
            )
        
        # Top performer insight
        if scores and scores[0].effectiveness_score > 90:
            recommendations.append(
                f"'{scores[0].title[:50]}' has {scores[0].effectiveness_score:.0f}% effectiveness - "
                "use as model for new test design"
            )
        
        return recommendations


# Singleton instance
test_effectiveness_tracker = TestEffectivenessTracker()


def calculate_effectiveness(
    suite_id: Optional[int] = None,
    recalculate: bool = False
) -> Dict[str, Any]:
    """Calculate test effectiveness scores."""
    return test_effectiveness_tracker.calculate_scores(suite_id, recalculate)


def get_case_effectiveness(case_id: int) -> Optional[Dict[str, Any]]:
    """Get effectiveness details for a case."""
    return test_effectiveness_tracker.get_case_details(case_id)


def get_effectiveness_trends(
    case_id: Optional[int] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Get effectiveness trends."""
    return test_effectiveness_tracker.get_trends(case_id, days)


def record_correlation(
    case_id: int,
    run_id: int,
    rca_id: str,
    correlation_type: str
):
    """Record a test-incident correlation."""
    test_effectiveness_tracker.record_correlation(case_id, run_id, rca_id, correlation_type)
