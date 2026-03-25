"""
Secrets Manager abstraction for enterprise credential management.

Supports multiple backends:
- Environment variables (default)
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

Provides automatic refresh capability when credentials rotate.
"""

import os
import json
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a secret cannot be found in the backend."""
    pass


class SecretRefreshError(Exception):
    """Raised when secret refresh fails."""
    pass


class SecretsBackend(ABC):
    """Abstract base class for secrets backends."""
    
    @abstractmethod
    def get_secret(self, key: str) -> str:
        """Retrieve a secret value by key."""
        pass
    
    @abstractmethod
    def refresh(self) -> bool:
        """Refresh credentials from the backend. Returns True if successful."""
        pass


class EnvSecretsBackend(SecretsBackend):
    """Environment variable backend (default, no refresh capability)."""
    
    def get_secret(self, key: str) -> str:
        value = os.getenv(key, "")
        if not value:
            logger.warning("secret_not_found_in_env", key=key)
        return value
    
    def refresh(self) -> bool:
        return True  # No-op for env vars


class AWSSecretsBackend(SecretsBackend):
    """AWS Secrets Manager backend with automatic refresh."""
    
    def __init__(self, secret_name: str, region: str = "us-east-1"):
        self.secret_name = secret_name
        self.region = region
        self._cache: Dict[str, str] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
    
    def get_secret(self, key: str) -> str:
        if self._should_refresh():
            self.refresh()
        return self._cache.get(key, "")
    
    def _should_refresh(self) -> bool:
        if not self._cache_time:
            return True
        return datetime.utcnow() - self._cache_time > self._cache_ttl
    
    def refresh(self) -> bool:
        try:
            import boto3
            client = boto3.client("secretsmanager", region_name=self.region)
            response = client.get_secret_value(SecretId=self.secret_name)
            secret_data = json.loads(response["SecretString"])
            self._cache = secret_data
            self._cache_time = datetime.utcnow()
            logger.info("aws_secrets_refreshed", secret_name=self.secret_name)
            return True
        except ImportError:
            logger.error("boto3_not_installed")
            return False
        except Exception as e:
            logger.error("aws_secrets_refresh_failed", error=str(e))
            return False


class VaultSecretsBackend(SecretsBackend):
    """HashiCorp Vault backend with automatic refresh."""
    
    def __init__(self, vault_url: str, mount_point: str = "secret", path: str = "paramount-mcp"):
        self.vault_url = vault_url
        self.mount_point = mount_point
        self.path = path
        self._cache: Dict[str, str] = {}
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        self._token = os.getenv("VAULT_TOKEN", "")
    
    def get_secret(self, key: str) -> str:
        if self._should_refresh():
            self.refresh()
        return self._cache.get(key, "")
    
    def _should_refresh(self) -> bool:
        if not self._cache_time:
            return True
        return datetime.utcnow() - self._cache_time > self._cache_ttl
    
    def refresh(self) -> bool:
        try:
            import hvac
            client = hvac.Client(url=self.vault_url, token=self._token)
            response = client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point,
                path=self.path
            )
            self._cache = response["data"]["data"]
            self._cache_time = datetime.utcnow()
            logger.info("vault_secrets_refreshed", path=self.path)
            return True
        except ImportError:
            logger.error("hvac_not_installed")
            return False
        except Exception as e:
            logger.error("vault_secrets_refresh_failed", error=str(e))
            return False


class SecretsManager:
    """
    Unified secrets manager with automatic refresh and fallback.
    
    Usage:
        secrets = SecretsManager()
        api_key = secrets.get("NEWRELIC_API_KEY")
        
        # Force refresh when auth fails
        secrets.refresh()
        api_key = secrets.get("NEWRELIC_API_KEY")
    """
    
    _instance: Optional["SecretsManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._backend = self._create_backend()
        self._refresh_callbacks: list[Callable[[], None]] = []
        self._last_refresh = datetime.utcnow()
        self._initialized = True
        
        logger.info("secrets_manager_initialized", backend=type(self._backend).__name__)
    
    def _create_backend(self) -> SecretsBackend:
        """Create the appropriate backend based on configuration."""
        backend_type = os.getenv("SECRETS_BACKEND", "env").lower()
        
        if backend_type == "aws":
            secret_name = os.getenv("AWS_SECRET_NAME", "paramount-mcp/credentials")
            region = os.getenv("AWS_REGION", "us-east-1")
            return AWSSecretsBackend(secret_name, region)
        
        elif backend_type == "vault":
            vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
            return VaultSecretsBackend(vault_url)
        
        else:
            return EnvSecretsBackend()
    
    def get(self, key: str, default: str = "") -> str:
        """
        Get a secret value, falling back to env var if backend fails.
        
        Args:
            key: The secret key (e.g., "NEWRELIC_API_KEY")
            default: Default value if not found
            
        Returns:
            The secret value
        """
        try:
            value = self._backend.get_secret(key)
            if value:
                return value
        except Exception as e:
            logger.warning("secret_backend_error", key=key, error=str(e))
        
        # Fallback to environment variable
        return os.getenv(key, default)
    
    def refresh(self) -> bool:
        """
        Force refresh all secrets from the backend.
        Call this when you detect an auth failure that might be due to rotated credentials.
        
        Returns:
            True if refresh succeeded
        """
        success = self._backend.refresh()
        self._last_refresh = datetime.utcnow()
        
        if success:
            for callback in self._refresh_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error("refresh_callback_failed", error=str(e))
        
        return success
    
    def on_refresh(self, callback: Callable[[], None]):
        """Register a callback to be called when secrets are refreshed."""
        self._refresh_callbacks.append(callback)
    
    @property
    def last_refresh(self) -> datetime:
        """When secrets were last refreshed."""
        return self._last_refresh


# Global singleton
secrets = SecretsManager()


def get_secret(key: str, default: str = "") -> str:
    """Convenience function to get a secret."""
    return secrets.get(key, default)


def refresh_secrets() -> bool:
    """Convenience function to refresh all secrets."""
    return secrets.refresh()
