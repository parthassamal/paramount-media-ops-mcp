"""
Example Configuration for Paramount+ MCP Server.

Copy this file to config.py and customize as needed.
Alternatively, set environment variables or create a .env file.

All configuration options support environment variable overrides.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Environment variables take precedence over default values.
    Create a .env file in the project root to override settings.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==========================================================================
    # Server Configuration
    # ==========================================================================
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8000
    mcp_server_name: str = "paramount-media-ops-mcp"
    mcp_server_version: str = "0.1.0"
    
    # Environment: development, staging, production
    environment: Literal["development", "staging", "production"] = "development"
    
    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    
    # Mock Mode - when True, uses generated data instead of real APIs
    mock_mode: bool = True
    
    # ==========================================================================
    # JIRA Configuration
    # Production issue tracking and workflow management
    # ==========================================================================
    jira_enabled: bool = True
    jira_api_url: str = Field(
        default="https://your-domain.atlassian.net",
        description="JIRA instance URL"
    )
    jira_api_email: str = Field(
        default="",
        description="JIRA account email for API authentication"
    )
    jira_api_token: str = Field(
        default="",
        description="JIRA API token"
    )
    jira_project_key: str = Field(
        default="PROD",
        description="Default JIRA project key"
    )
    jira_request_timeout: int = 30
    
    # ==========================================================================
    # Conviva Configuration
    # Streaming Quality of Experience (QoE) analytics
    # ==========================================================================
    conviva_enabled: bool = True
    conviva_api_url: str = Field(
        default="https://api.conviva.com/insights/2.4",
        description="Conviva Insights API base URL"
    )
    conviva_customer_key: str = Field(
        default="",
        description="Conviva customer key"
    )
    conviva_api_key: str = Field(
        default="",
        description="Conviva API key"
    )
    conviva_request_timeout: int = 60
    
    # Conviva alert thresholds
    conviva_buffering_threshold: float = 0.02  # 2%
    conviva_vsf_threshold: float = 0.05  # 5%
    conviva_ebvs_threshold: float = 0.03  # 3%
    
    # ==========================================================================
    # NewRelic Configuration
    # Application Performance Monitoring (APM) and Infrastructure
    # ==========================================================================
    newrelic_enabled: bool = True
    newrelic_api_url: str = Field(
        default="https://api.newrelic.com/graphql",
        description="NewRelic GraphQL API URL"
    )
    newrelic_insights_api_url: str = Field(
        default="https://insights-api.newrelic.com/v1",
        description="NewRelic Insights API URL"
    )
    newrelic_api_key: str = Field(
        default="",
        description="NewRelic API key"
    )
    newrelic_account_id: str = Field(
        default="",
        description="NewRelic account ID"
    )
    newrelic_request_timeout: int = 30
    
    # NewRelic alert thresholds
    newrelic_error_rate_threshold: float = 0.01  # 1%
    newrelic_apdex_threshold: float = 0.85
    newrelic_response_time_threshold: float = 2.0  # seconds
    
    # ==========================================================================
    # Internal Analytics Configuration
    # ==========================================================================
    analytics_enabled: bool = True
    analytics_api_url: str = "https://analytics.your-domain.com/api/v2"
    analytics_api_key: str = ""
    analytics_request_timeout: int = 30
    
    # ==========================================================================
    # Content API Configuration
    # ==========================================================================
    content_api_url: str = "https://content.your-domain.com/api/v1"
    content_api_key: str = ""
    
    # ==========================================================================
    # Email Configuration (optional)
    # ==========================================================================
    email_enabled: bool = False
    email_imap_server: str = "imap.your-domain.com"
    email_imap_port: int = 993
    email_username: str = ""
    email_password: str = ""
    email_folder: str = "INBOX"
    
    # ==========================================================================
    # LLM Configuration (optional)
    # ==========================================================================
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    # ==========================================================================
    # Data Configuration
    # ==========================================================================
    random_seed: int = 42  # For reproducible mock data
    pareto_threshold: float = 0.80  # 80% for Pareto analysis
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Database
    database_url: str = "sqlite:///./paramount_ops.db"
    
    # ==========================================================================
    # Helper Properties
    # ==========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_environment_display(self) -> str:
        """Get display name for current environment."""
        env_display = {
            "development": "🔧 Development",
            "staging": "🧪 Staging",
            "production": "🚀 Production"
        }
        return env_display.get(self.environment, self.environment)


# ==========================================================================
# Factory function for environment-specific settings
# ==========================================================================

def get_settings() -> Settings:
    """
    Factory function to get environment-appropriate settings.
    
    Reads ENVIRONMENT variable to determine configuration.
    """
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        # Production: disable mock mode, increase cache TTL
        return Settings(
            environment="production",
            mock_mode=False,
            log_level="WARNING",
            log_format="json",
            cache_ttl_seconds=600
        )
    elif env == "staging":
        # Staging: disable mock mode, use INFO logging
        return Settings(
            environment="staging",
            mock_mode=False,
            log_level="INFO",
            log_format="json"
        )
    else:
        # Development: enable mock mode, verbose logging
        return Settings(
            environment="development",
            mock_mode=True,
            log_level="DEBUG",
            log_format="text"
        )


# Global settings instance
settings = get_settings()
