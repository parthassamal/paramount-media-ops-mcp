"""
Configuration file for Paramount+ MCP Server
Copy this to config.py and customize as needed
"""
import os
from typing import Optional


class Config:
    """Server configuration"""
    
    # JIRA Configuration (optional - uses mock data if not provided)
    JIRA_SERVER: Optional[str] = os.getenv("JIRA_SERVER")
    JIRA_EMAIL: Optional[str] = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN")
    
    # LLM Configuration (optional - for enhanced analysis)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Data Generation Settings
    DEFAULT_COHORT_SIZE: int = 100
    DEFAULT_ISSUE_COUNT: int = 50
    DEFAULT_COMPLAINT_COUNT: int = 100
    
    # Pareto Analysis Settings
    PARETO_THRESHOLD: float = 0.8  # 80% threshold for Pareto analysis
    
    # Server Settings
    SERVER_NAME: str = "paramount-media-ops"
    VERSION: str = "1.0.0"


# Singleton instance
config = Config()
