"""Tests for Email Parser"""
import pytest
from src.email_parser import EmailParser


def test_email_parser_initialization():
    """Test email parser initialization"""
    parser = EmailParser()
    assert parser is not None


def test_analyze_complaint_text():
    """Test complaint text analysis"""
    parser = EmailParser()
    
    # Test streaming issue
    result = parser._analyze_complaint_text("The video keeps buffering and freezing")
    assert "topic" in result
    assert result["topic"].lower() in ["streaming", "quality"]
    
    # Test billing issue
    result = parser._analyze_complaint_text("I was charged twice for my subscription")
    assert result["topic"].lower() == "billing"


def test_get_mock_complaints():
    """Test mock complaint generation"""
    parser = EmailParser()
    complaints = parser.get_mock_complaints(25)
    
    assert len(complaints) == 25
    assert all("complaint_id" in c for c in complaints)
    assert all("topic" in c for c in complaints)


def test_analyze_complaints_with_pareto():
    """Test Pareto analysis of complaints"""
    parser = EmailParser()
    complaints = parser.get_mock_complaints(50)
    pareto_result = parser.analyze_complaints_with_pareto(complaints)
    
    assert "vital_few" in pareto_result
    assert "pareto_insight" in pareto_result
    assert len(pareto_result["vital_few"]) > 0


def test_analyze_sentiment_trends():
    """Test sentiment analysis"""
    parser = EmailParser()
    complaints = parser.get_mock_complaints(30)
    sentiment = parser.analyze_sentiment_trends(complaints)
    
    assert "average_sentiment" in sentiment
    assert "negative_percentage" in sentiment
    assert "positive_percentage" in sentiment
    assert sentiment["total_complaints"] == 30


def test_get_critical_complaint_topics():
    """Test getting critical topics"""
    parser = EmailParser()
    complaints = parser.get_mock_complaints(40)
    critical = parser.get_critical_complaint_topics(complaints)
    
    assert len(critical) > 0
    assert all("topic" in item for item in critical)
    assert all("count" in item for item in critical)


def test_parse_email():
    """Test email parsing"""
    parser = EmailParser()
    
    email_content = """From: customer@example.com
To: support@paramount.com
Subject: Buffering Issues
Date: Mon, 01 Jan 2025 12:00:00 +0000

I'm experiencing constant buffering issues while trying to watch content.
This is urgent and needs to be fixed immediately.
"""
    
    result = parser.parse_email(email_content)
    
    assert "complaint_id" in result
    assert "topic" in result
    assert "sentiment_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
