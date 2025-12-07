"""
Email parser with NLP complaint clustering.

Provides interface to parse emails and cluster complaints by theme.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings
from mcp.mocks.generate_complaint_data import ComplaintDataGenerator


class EmailParser:
    """
    Email parser with NLP-based complaint clustering.
    
    In mock mode, returns generated data. In production, connects to email server
    and performs NLP analysis.
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize email parser.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.imap_server = settings.email_imap_server
        self.username = settings.email_username
        self.password = settings.email_password
        
        if self.mock_mode:
            self.generator = ComplaintDataGenerator()
    
    def get_complaint_themes(
        self,
        days_back: int = 30,
        min_volume: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get clustered complaint themes from emails.
        
        Args:
            days_back: Number of days to analyze (default: 30)
            min_volume: Minimum complaint volume to include theme
        
        Returns:
            List of complaint theme dictionaries
        """
        if self.mock_mode:
            return self._get_mock_themes(min_volume)
        else:
            return self._parse_and_cluster(days_back, min_volume)
    
    def _get_mock_themes(self, min_volume: int) -> List[Dict[str, Any]]:
        """Get mock complaint themes."""
        themes = self.generator.generate_themes(num_themes=10)
        
        # Filter by minimum volume
        return [t for t in themes if t["complaint_volume"] >= min_volume]
    
    def _parse_and_cluster(self, days_back: int, min_volume: int) -> List[Dict[str, Any]]:
        """Parse emails and perform NLP clustering."""
        # TODO: Implement real email parsing and NLP clustering
        # This would use:
        # - imaplib for email retrieval
        # - scikit-learn for text clustering (KMeans, DBSCAN)
        # - Sentiment analysis (TextBlob or transformers)
        raise NotImplementedError("Real email parsing not yet implemented. Use mock_mode=True.")
    
    def get_individual_complaints(
        self,
        theme_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get individual complaint tickets.
        
        Args:
            theme_id: Filter by theme ID (optional)
            limit: Maximum number of complaints to return
        
        Returns:
            List of individual complaint dictionaries
        """
        if self.mock_mode:
            themes = self._get_mock_themes(min_volume=0)
            complaints = self.generator.generate_individual_complaints(themes, count=limit)
            
            if theme_id:
                complaints = [c for c in complaints if c["theme_id"] == theme_id]
            
            return complaints[:limit]
        else:
            raise NotImplementedError("Real email parsing not yet implemented. Use mock_mode=True.")
    
    def get_sentiment_trends(self, days_back: int = 90) -> Dict[str, Any]:
        """
        Get sentiment trends over time.
        
        Args:
            days_back: Number of days to analyze
        
        Returns:
            Sentiment trends dictionary
        """
        themes = self.get_complaint_themes(days_back=days_back)
        
        avg_sentiment = sum(t["avg_sentiment_score"] for t in themes) / len(themes) if themes else 0
        
        # Group themes by sentiment range
        sentiment_distribution = {
            "very_negative": len([t for t in themes if t["avg_sentiment_score"] <= -0.7]),
            "negative": len([t for t in themes if -0.7 < t["avg_sentiment_score"] <= -0.4]),
            "neutral": len([t for t in themes if -0.4 < t["avg_sentiment_score"] <= 0.4]),
            "positive": len([t for t in themes if t["avg_sentiment_score"] > 0.4])
        }
        
        return {
            "avg_sentiment": round(avg_sentiment, 2),
            "sentiment_distribution": sentiment_distribution,
            "most_negative_theme": min(themes, key=lambda x: x["avg_sentiment_score"]) if themes else None,
            "total_complaints": sum(t["complaint_volume"] for t in themes)
        }
    
    def get_churn_correlation_analysis(self) -> Dict[str, Any]:
        """
        Analyze correlation between complaint themes and churn.
        
        Returns:
            Churn correlation analysis
        """
        themes = self.get_complaint_themes()
        
        # Sort by churn correlation
        sorted_themes = sorted(themes, key=lambda x: x["churn_correlation"], reverse=True)
        
        high_correlation_themes = [t for t in themes if t["churn_correlation"] >= 0.5]
        
        total_churners = sum(t["churners_attributed"] for t in themes)
        high_correlation_churners = sum(t["churners_attributed"] for t in high_correlation_themes)
        
        return {
            "total_themes": len(themes),
            "high_correlation_themes": len(high_correlation_themes),
            "total_churners_attributed": total_churners,
            "high_correlation_contribution": round(
                high_correlation_churners / total_churners, 2
            ) if total_churners > 0 else 0,
            "top_churn_drivers": [
                {
                    "theme_name": t["name"],
                    "churn_correlation": t["churn_correlation"],
                    "churners_attributed": t["churners_attributed"]
                }
                for t in sorted_themes[:3]
            ]
        }
