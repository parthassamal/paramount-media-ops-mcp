"""Email Parser with NLP for Complaint Analysis"""
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from email.parser import Parser
from email.policy import default
from textblob import TextBlob
from collections import Counter
from src.pareto_engine import ParetoAnalyzer
from src.mock_data import MockDataGenerator


class EmailParser:
    """Parse and analyze customer complaint emails using NLP"""
    
    COMPLAINT_KEYWORDS = {
        "streaming": ["buffer", "lag", "freeze", "stuttering", "slow", "loading"],
        "content": ["missing", "unavailable", "removed", "not found", "can't find"],
        "billing": ["charge", "payment", "refund", "subscription", "cancel", "price"],
        "technical": ["error", "crash", "bug", "broken", "not working", "issue"],
        "quality": ["quality", "resolution", "pixelated", "blurry", "audio", "video"],
        "account": ["login", "password", "access", "locked", "authentication"],
        "service": ["support", "customer service", "response", "help", "assistance"]
    }
    
    def __init__(self):
        """Initialize the email parser"""
        self.complaints = []
    
    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """
        Parse an email and extract complaint information
        
        Args:
            email_content: Raw email content
            
        Returns:
            Parsed complaint data
        """
        try:
            # Parse email
            msg = Parser(policy=default).parsestr(email_content)
            
            subject = msg.get('subject', 'No Subject')
            from_addr = msg.get('from', 'unknown@example.com')
            date_str = msg.get('date', datetime.now().isoformat())
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Analyze with NLP
            complaint_data = self._analyze_complaint_text(subject + " " + body)
            complaint_data.update({
                "complaint_id": f"CMP-{hash(email_content) % 100000:05d}",
                "subject": subject,
                "from": from_addr,
                "received_date": date_str,
                "channel": "Email"
            })
            
            return complaint_data
            
        except Exception as e:
            return {
                "complaint_id": "CMP-ERROR",
                "error": str(e),
                "topic": "Unknown",
                "sentiment_score": 0
            }
    
    def _analyze_complaint_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze complaint text using NLP
        
        Args:
            text: Complaint text
            
        Returns:
            Analysis results
        """
        # Sentiment analysis
        blob = TextBlob(text.lower())
        sentiment_score = blob.sentiment.polarity
        
        # Topic classification based on keywords
        topics = []
        topic_scores = {}
        
        for category, keywords in self.COMPLAINT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text.lower())
            if score > 0:
                topic_scores[category] = score
                topics.append(category)
        
        # Get primary topic
        primary_topic = max(topic_scores.items(), key=lambda x: x[1])[0] if topic_scores else "general"
        
        # Extract urgency indicators
        urgency_keywords = ["urgent", "immediately", "asap", "critical", "emergency"]
        urgency_count = sum(1 for keyword in urgency_keywords if keyword in text.lower())
        
        urgency_level = "Critical" if urgency_count >= 2 else \
                       "High" if urgency_count == 1 else \
                       "Medium" if sentiment_score < -0.5 else "Low"
        
        return {
            "topic": primary_topic.title(),
            "all_topics": topics,
            "sentiment_score": round(sentiment_score, 3),
            "urgency_level": urgency_level,
            "text_snippet": text[:200] + "..." if len(text) > 200 else text,
            "word_count": len(text.split())
        }
    
    def parse_complaint_batch(self, email_contents: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple emails
        
        Args:
            email_contents: List of email contents
            
        Returns:
            List of parsed complaints
        """
        complaints = []
        for email_content in email_contents:
            complaint = self.parse_email(email_content)
            complaints.append(complaint)
        
        self.complaints.extend(complaints)
        return complaints
    
    def get_mock_complaints(self, num_complaints: int = 100) -> List[Dict[str, Any]]:
        """Generate mock complaint data"""
        return MockDataGenerator.generate_complaint_themes(num_complaints)
    
    def analyze_complaints_with_pareto(self, complaints: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze complaints using Pareto principle
        
        Args:
            complaints: List of complaints (if None, uses stored or generates mock)
            
        Returns:
            Pareto analysis results grouped by topic
        """
        if complaints is None:
            complaints = self.complaints if self.complaints else self.get_mock_complaints()
        
        # Aggregate by topic
        topic_counts = Counter(c.get("topic", "Unknown") for c in complaints)
        
        # Convert to format for Pareto analysis
        topic_data = [
            {"topic": topic, "count": count}
            for topic, count in topic_counts.items()
        ]
        
        return ParetoAnalyzer.analyze(topic_data, "count", "topic")
    
    def get_critical_complaint_topics(self, complaints: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Get the vital few complaint topics using Pareto analysis"""
        pareto_result = self.analyze_complaints_with_pareto(complaints)
        return pareto_result["vital_few"]
    
    def analyze_sentiment_trends(self, complaints: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze sentiment trends across complaints
        
        Args:
            complaints: List of complaints
            
        Returns:
            Sentiment analysis summary
        """
        if complaints is None:
            complaints = self.complaints if self.complaints else self.get_mock_complaints()
        
        sentiments = [c.get("sentiment_score", 0) for c in complaints if "sentiment_score" in c]
        
        if not sentiments:
            return {"error": "No sentiment data available"}
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        negative_count = sum(1 for s in sentiments if s < -0.1)
        neutral_count = sum(1 for s in sentiments if -0.1 <= s <= 0.1)
        positive_count = sum(1 for s in sentiments if s > 0.1)
        
        return {
            "total_complaints": len(complaints),
            "average_sentiment": round(avg_sentiment, 3),
            "negative_percentage": round(negative_count / len(complaints) * 100, 2),
            "neutral_percentage": round(neutral_count / len(complaints) * 100, 2),
            "positive_percentage": round(positive_count / len(complaints) * 100, 2),
            "sentiment_distribution": {
                "negative": negative_count,
                "neutral": neutral_count,
                "positive": positive_count
            }
        }
