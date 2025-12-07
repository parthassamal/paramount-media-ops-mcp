"""
Configuration module for Paramount Media Operations MCP Server.

This module centralizes all configuration settings using pydantic-settings
for type-safe configuration management with environment variable support.

Supports multiple environments (development, staging, production) and
integrations with JIRA, Conviva, NewRelic, and internal analytics systems.
"""

from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
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
        default="https://paramount.atlassian.net",
        description="JIRA instance URL"
    )
    jira_api_email: str = Field(
        default="",
        description="JIRA account email for API authentication"
    )
    jira_api_token: str = Field(
        default="",
        description="JIRA API token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)"
    )
    jira_project_key: str = Field(
        default="PROD",
        description="Default JIRA project key for production issues"
    )
    jira_content_project_key: str = Field(
        default="CONTENT",
        description="JIRA project key for content/show issues"
    )
    jira_issue_types: str = Field(
        default="Bug,Task,Story,Epic",
        description="Comma-separated list of issue types to track"
    )
    jira_custom_field_cost_impact: str = Field(
        default="customfield_10001",
        description="Custom field ID for cost impact"
    )
    jira_custom_field_delay_days: str = Field(
        default="customfield_10002",
        description="Custom field ID for delay days"
    )
    jira_custom_field_show_name: str = Field(
        default="customfield_10003",
        description="Custom field ID for associated show"
    )
    jira_request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
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
        description="Conviva customer key (account identifier)"
    )
    conviva_api_key: str = Field(
        default="",
        description="Conviva API key for authentication"
    )
    conviva_filter_client: str = Field(
        default="paramount-plus",
        description="Filter for specific client/app"
    )
    conviva_metrics: str = Field(
        default="plays,concurrent_plays,buffering_ratio,video_start_failures,exits_before_video_start,average_bitrate,rebuffering_ratio",
        description="Comma-separated metrics to fetch"
    )
    conviva_dimensions: str = Field(
        default="device_type,os,country,isp,cdn,content_type",
        description="Comma-separated dimensions for grouping"
    )
    conviva_request_timeout: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    
    # Conviva alert thresholds
    conviva_buffering_threshold: float = Field(
        default=0.02,
        description="Buffering ratio threshold for alerts (2%)"
    )
    conviva_vsf_threshold: float = Field(
        default=0.05,
        description="Video Start Failure threshold for alerts (5%)"
    )
    conviva_ebvs_threshold: float = Field(
        default=0.03,
        description="Exits Before Video Start threshold for alerts (3%)"
    )
    
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
        description="NewRelic Insights API URL for NRQL queries"
    )
    newrelic_api_key: str = Field(
        default="",
        description="NewRelic API key (User key or License key)"
    )
    newrelic_account_id: str = Field(
        default="",
        description="NewRelic account ID"
    )
    newrelic_app_name: str = Field(
        default="paramount-plus-streaming",
        description="NewRelic application name to monitor"
    )
    newrelic_request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # NewRelic alert thresholds
    newrelic_error_rate_threshold: float = Field(
        default=0.01,
        description="Error rate threshold for alerts (1%)"
    )
    newrelic_apdex_threshold: float = Field(
        default=0.85,
        description="Apdex score threshold for alerts"
    )
    newrelic_response_time_threshold: float = Field(
        default=2.0,
        description="Response time threshold in seconds"
    )
    
    # ==========================================================================
    # Internal Analytics Configuration
    # Paramount+ subscriber and content analytics
    # ==========================================================================
    analytics_enabled: bool = True
    analytics_api_url: str = Field(
        default="https://analytics.paramount.com/api/v2",
        description="Internal analytics API URL"
    )
    analytics_api_key: str = Field(
        default="",
        description="Analytics API key"
    )
    analytics_request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # ==========================================================================
    # Content API Configuration
    # Content catalog and metadata
    # ==========================================================================
    content_api_url: str = Field(
        default="https://content.paramount.com/api/v1",
        description="Content catalog API URL"
    )
    content_api_key: str = Field(
        default="",
        description="Content API key"
    )
    
    # ==========================================================================
    # Email Configuration
    # Support email parsing for complaint analysis
    # ==========================================================================
    email_enabled: bool = False
    email_imap_server: str = Field(
        default="imap.paramount.com",
        description="IMAP server for email ingestion"
    )
    email_imap_port: int = Field(
        default=993,
        description="IMAP server port (993 for SSL)"
    )
    email_username: str = ""
    email_password: str = ""
    email_folder: str = Field(
        default="INBOX",
        description="Email folder to monitor"
    )
    
    # ==========================================================================
    # LLM Configuration
    # AI/ML integrations
    # ==========================================================================
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    
    # ==========================================================================
    # Data Configuration
    # ==========================================================================
    random_seed: int = 42
    pareto_threshold: float = 0.80
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds (5 minutes default)"
    )
    
    # Database
    database_url: str = "sqlite:///./paramount_ops.db"
    
    # ==========================================================================
    # Environment-Specific Presets
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
# Environment-Specific Configuration Presets
# ==========================================================================

class DevelopmentSettings(Settings):
    """Development environment defaults."""
    environment: Literal["development", "staging", "production"] = "development"
    mock_mode: bool = True
    log_level: str = "DEBUG"
    log_format: Literal["json", "text"] = "text"


class StagingSettings(Settings):
    """Staging environment defaults."""
    environment: Literal["development", "staging", "production"] = "staging"
    mock_mode: bool = False
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    
    # Staging URLs (override in .env)
    jira_api_url: str = "https://paramount-staging.atlassian.net"
    conviva_api_url: str = "https://api.conviva.com/insights/2.4"
    analytics_api_url: str = "https://analytics-staging.paramount.com/api/v2"


class ProductionSettings(Settings):
    """Production environment defaults."""
    environment: Literal["development", "staging", "production"] = "production"
    mock_mode: bool = False
    log_level: str = "WARNING"
    log_format: Literal["json", "text"] = "json"
    cache_enabled: bool = True
    cache_ttl_seconds: int = 600  # 10 minutes in production


def get_settings() -> Settings:
    """
    Factory function to get environment-appropriate settings.
    
    Reads ENVIRONMENT variable to determine which settings class to use.
    """
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "staging":
        return StagingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()
