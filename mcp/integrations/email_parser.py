"""
Email parser with NLP complaint clustering.

Provides interface to parse emails and cluster complaints by theme.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings
from mcp.mocks.generate_complaint_data import ComplaintDataGenerator
from mcp.utils.error_handler import ConnectionError, ValidationError, retry_with_backoff
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)


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
        """
        Parse emails and perform NLP clustering using sklearn + spaCy.
        
        Real implementation using:
        - TF-IDF vectorization for text representation
        - DBSCAN clustering (better than K-Means for unknown cluster count)
        - spaCy for keyword extraction
        - TextBlob for sentiment analysis
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import DBSCAN
        import numpy as np
        from mcp.ai.nlp_engine import get_nlp_engine
        
        # Initialize NLP engine
        nlp_engine = get_nlp_engine()
        
        # Fetch emails from IMAP server
        emails = self._fetch_emails_imap(days_back)
        
        if len(emails) == 0:
            return []
        
        # Extract text from emails
        texts = [self._preprocess_email_text(email['body']) for email in emails]
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=200,
            stop_words='english',
            min_df=2,
            max_df=0.8
        )
        
        vectors = vectorizer.fit_transform(texts)
        
        # DBSCAN clustering (automatically determines number of clusters)
        clusterer = DBSCAN(eps=0.5, min_samples=3, metric='cosine')
        labels = clusterer.fit_predict(vectors)
        
        # Extract themes from clusters
        themes = []
        unique_labels = set(labels)
        
        for cluster_id in unique_labels:
            if cluster_id == -1:
                # Noise cluster - skip
                continue
            
            # Get documents in this cluster
            cluster_mask = labels == cluster_id
            cluster_texts = [texts[i] for i, is_in_cluster in enumerate(cluster_mask) if is_in_cluster]
            cluster_emails = [emails[i] for i, is_in_cluster in enumerate(cluster_mask) if is_in_cluster]
            
            # Skip small clusters
            if len(cluster_texts) < min_volume:
                continue
            
            # Extract theme name and keywords
            theme_name, keywords = self._extract_theme_info(cluster_texts, nlp_engine)
            
            # Calculate average sentiment
            sentiments = [nlp_engine.analyze_sentiment(text) for text in cluster_texts]
            avg_sentiment = float(np.mean(sentiments))
            
            # Build theme dict
            theme = {
                "theme_id": f"THEME-{cluster_id}",
                "name": theme_name,
                "complaint_volume": len(cluster_texts),
                "avg_sentiment": avg_sentiment,
                "sentiment_label": "negative" if avg_sentiment < -0.2 else "neutral" if avg_sentiment < 0.2 else "positive",
                "keywords": keywords,
                "sample_complaints": cluster_texts[:5]  # First 5 as samples
            }
            
            themes.append(theme)
        
        # Sort by volume descending
        themes.sort(key=lambda x: x['complaint_volume'], reverse=True)
        
        return themes
    
    def _fetch_emails_imap(self, days_back: int) -> List[Dict[str, Any]]:
        """
        Fetch emails from IMAP server.
        
        Args:
            days_back: Number of days to fetch
            
        Returns:
            List of email dicts with subject, body, date
        """
        try:
            import imaplib
            import email
            from email.header import decode_header
            from datetime import datetime, timedelta
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.username, self.password)
            mail.select(settings.email_folder)
            
            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search for emails
            _, message_numbers = mail.search(None, f'(SINCE {since_date})')
            
            emails = []
            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")
                        
                        # Extract body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        emails.append({
                            "subject": subject,
                            "body": body,
                            "date": msg["Date"]
                        })
            
            mail.close()
            mail.logout()
            
            return emails
        except Exception as e:
            # If IMAP fails, return empty list
            # In production, would log error
            return []
    
    def _preprocess_email_text(self, text: str) -> str:
        """Preprocess email text for analysis."""
        import re
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_theme_info(
        self,
        texts: List[str],
        nlp_engine
    ) -> tuple[str, List[str]]:
        """
        Extract theme name and keywords from cluster texts.
        
        Args:
            texts: List of text documents in cluster
            nlp_engine: NLP engine instance
            
        Returns:
            Tuple of (theme_name, keywords)
        """
        # Combine all texts
        combined_text = ' '.join(texts)
        
        # Extract keywords
        keywords = nlp_engine.extract_keywords(combined_text, top_k=10)
        
        # Generate theme name from top 2-3 keywords
        theme_name = ' '.join(keywords[:3]).title()
        
        return theme_name, keywords
    
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
