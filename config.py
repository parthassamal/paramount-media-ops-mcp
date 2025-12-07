"""
Configuration module for Paramount Media Operations MCP Server.

This module centralizes all configuration settings using pydantic-settings
for type-safe configuration management with environment variable support.
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Server Configuration
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8000
    mcp_server_name: str = "paramount-media-ops-mcp"
    mcp_server_version: str = "0.1.0"
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    
    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    
    # Mock Mode
    mock_mode: bool = True
    
    # External API Configuration
    jira_api_url: str = "https://paramount.atlassian.net"
    jira_api_token: str = ""
    jira_project_key: str = "PROD"
    
    email_imap_server: str = "imap.paramount.com"
    email_username: str = ""
    email_password: str = ""
    
    analytics_api_url: str = "https://analytics.paramount.com"
    analytics_api_key: str = ""
    
    content_api_url: str = "https://content.paramount.com/api/v1"
    content_api_key: str = ""
    
    # Anthropic API
    anthropic_api_key: str = ""
    
    # Data Configuration
    random_seed: int = 42
    pareto_threshold: float = 0.80
    
    # Database
    database_url: str = "sqlite:///./paramount_ops.db"


# Global settings instance
settings = Settings()
