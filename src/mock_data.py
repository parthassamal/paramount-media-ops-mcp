"""Mock Data Generators for Paramount+ Operations"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


class MockDataGenerator:
    """Generates realistic mock data for various operational scenarios"""
    
    # Sample data pools
    TITLES = [
        "Star Trek: Strange New Worlds", "Yellowstone", "1883", "Mayor of Kingstown",
        "Tulsa King", "SEAL Team", "Paramount+ Original Movie", "Comedy Special",
        "UEFA Champions League", "NFL on CBS", "The Challenge", "RuPaul's Drag Race"
    ]
    
    GENRES = ["Drama", "Action", "Comedy", "Reality", "Sports", "Documentary", "Sci-Fi"]
    
    MARKETS = [
        "United States", "United Kingdom", "Canada", "Australia", "Germany",
        "France", "Italy", "Spain", "Brazil", "Mexico", "India", "Japan"
    ]
    
    ISSUE_TYPES = [
        "Buffering/Streaming Quality", "Login/Authentication", "Payment Processing",
        "Content Unavailable", "Audio/Video Sync", "Subtitle Issues", "App Crash",
        "Download Failure", "Live Stream Lag", "UI/UX Bug"
    ]
    
    COMPLAINT_TOPICS = [
        "Poor Streaming Quality", "Content Not Available", "Billing Issues",
        "Technical Glitches", "Customer Service", "App Performance", 
        "Account Access", "Subscription Cancellation", "Content Recommendations"
    ]
    
    CHURN_REASONS = [
        "Content Library", "Technical Issues", "Price Sensitivity", "Competition",
        "Usage Frequency", "Content Discovery", "Quality Concerns", "Feature Limitations"
    ]
    
    @staticmethod
    def generate_churn_cohort(num_users: int = 100) -> List[Dict[str, Any]]:
        """Generate mock churn signal data"""
        cohort = []
        base_date = datetime.now()
        
        for i in range(num_users):
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            signup_date = base_date - timedelta(days=random.randint(30, 730))
            last_activity = base_date - timedelta(days=random.randint(0, 60))
            
            cohort.append({
                "user_id": user_id,
                "signup_date": signup_date.isoformat(),
                "last_activity_date": last_activity.isoformat(),
                "days_since_last_activity": (base_date - last_activity).days,
                "total_watch_hours": round(random.uniform(10, 500), 2),
                "avg_session_duration_minutes": round(random.uniform(15, 120), 2),
                "monthly_active_days": random.randint(1, 30),
                "content_diversity_score": round(random.uniform(0.1, 1.0), 2),
                "engagement_trend": random.choice(["declining", "stable", "increasing"]),
                "churn_risk_score": round(random.uniform(0, 1), 3),
                "predicted_churn_reason": random.choice(MockDataGenerator.CHURN_REASONS),
                "subscription_tier": random.choice(["Essential", "Premium", "Premium+"]),
                "market": random.choice(MockDataGenerator.MARKETS),
                "device_types": random.sample(["mobile", "tablet", "smart_tv", "desktop", "streaming_device"], k=random.randint(1, 3))
            })
        
        return cohort
    
    @staticmethod
    def generate_production_issues(num_issues: int = 50) -> List[Dict[str, Any]]:
        """Generate mock production issues"""
        issues = []
        base_date = datetime.now()
        
        for i in range(num_issues):
            issue_id = f"PROD-{random.randint(1000, 9999)}"
            created = base_date - timedelta(hours=random.randint(1, 168))
            
            severity = random.choice(["Critical", "High", "Medium", "Low"])
            severity_weights = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}
            
            affected_users = random.randint(10, 50000)
            revenue_impact = round(affected_users * random.uniform(0.5, 5.0), 2)
            
            issues.append({
                "issue_id": issue_id,
                "title": f"{random.choice(MockDataGenerator.ISSUE_TYPES)} - {random.choice(MockDataGenerator.TITLES)}",
                "type": random.choice(MockDataGenerator.ISSUE_TYPES),
                "severity": severity,
                "status": random.choice(["Open", "In Progress", "Resolved", "Monitoring"]),
                "created_date": created.isoformat(),
                "affected_users": affected_users,
                "estimated_revenue_impact": revenue_impact,
                "impact_score": severity_weights[severity] + (affected_users / 100),
                "content_title": random.choice(MockDataGenerator.TITLES),
                "market": random.choice(MockDataGenerator.MARKETS),
                "platform": random.choice(["iOS", "Android", "Web", "Smart TV", "Roku", "Fire TV"]),
                "resolution_time_hours": random.randint(1, 72) if random.random() > 0.3 else None,
                "assignee": f"engineer_{random.randint(1, 10)}"
            })
        
        return issues
    
    @staticmethod
    def generate_complaint_themes(num_complaints: int = 100) -> List[Dict[str, Any]]:
        """Generate mock complaint data with themes"""
        complaints = []
        base_date = datetime.now()
        
        for i in range(num_complaints):
            complaint_id = f"CMP-{uuid.uuid4().hex[:8]}"
            received = base_date - timedelta(hours=random.randint(1, 720))
            
            topic = random.choice(MockDataGenerator.COMPLAINT_TOPICS)
            sentiment_score = random.uniform(-1, 0.5)  # Complaints tend to be negative
            
            complaints.append({
                "complaint_id": complaint_id,
                "received_date": received.isoformat(),
                "topic": topic,
                "sentiment_score": round(sentiment_score, 3),
                "urgency_level": random.choice(["Low", "Medium", "High", "Critical"]),
                "channel": random.choice(["Email", "Social Media", "App Review", "Call Center", "Chat"]),
                "user_tenure_months": random.randint(1, 60),
                "resolution_status": random.choice(["Pending", "Acknowledged", "Resolved", "Escalated"]),
                "satisfaction_score": random.randint(1, 5) if random.random() > 0.4 else None,
                "related_content": random.choice(MockDataGenerator.TITLES) if random.random() > 0.5 else None,
                "market": random.choice(MockDataGenerator.MARKETS),
                "frequency_count": random.randint(1, 10),
                "text_snippet": f"Sample complaint about {topic.lower()}..."
            })
        
        return complaints
    
    @staticmethod
    def generate_content_catalog(num_titles: int = 50) -> List[Dict[str, Any]]:
        """Generate mock content catalog"""
        catalog = []
        base_date = datetime.now()
        
        for i in range(num_titles):
            title = f"{random.choice(MockDataGenerator.TITLES)} - S{random.randint(1, 5)}"
            release_date = base_date - timedelta(days=random.randint(1, 1825))
            
            catalog.append({
                "content_id": f"CNT-{uuid.uuid4().hex[:8]}",
                "title": title,
                "genre": random.choice(MockDataGenerator.GENRES),
                "release_date": release_date.isoformat(),
                "duration_minutes": random.randint(30, 180),
                "total_views": random.randint(1000, 5000000),
                "unique_viewers": random.randint(500, 2000000),
                "avg_watch_completion": round(random.uniform(0.3, 0.95), 2),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "production_cost_millions": round(random.uniform(0.5, 50), 2),
                "revenue_generated_millions": round(random.uniform(1, 100), 2),
                "roi": round(random.uniform(-0.5, 5.0), 2),
                "available_markets": random.sample(MockDataGenerator.MARKETS, k=random.randint(3, 10)),
                "licensing_expiry": (base_date + timedelta(days=random.randint(30, 730))).isoformat(),
                "popularity_trend": random.choice(["rising", "stable", "declining"])
            })
        
        return catalog
