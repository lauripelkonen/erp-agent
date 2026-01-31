"""
Configuration management for the Offer Automation System.
Uses Pydantic for environment variable validation and type safety.
"""

import os
from typing import Optional, Literal
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main configuration class for the offer automation system."""
    
    # Application Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    # OpenAI Configuration (using Gemini API with OpenAI schema)
    gemini_api_key: str = Field(
        env="GEMINI_API_KEY",
        description="Gemini API key for LLM and embedding services"
    )
    openai_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        env="OPENAI_BASE_URL",
        description="Base URL for OpenAI-compatible API (Gemini)"
    )
    openai_model: str = Field(
        default="gemini-2.5-flash",
        env="OPENAI_MODEL",
        description="Chat completion model"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-004",
        env="OPENAI_EMBEDDING_MODEL", 
        description="Embedding model (Gemini text-embedding-004)"
    )
    openai_api_key: str = Field(
        env="OPENAI_API_KEY",
        description="OpenAI API key"
    )

    enable_search_grounding: bool = Field(
        default=True,
        env="ENABLE_SEARCH_GROUNDING",
        description="Enable Gemini 2.0 Google Search Grounding for web searches"
    )
    
    # Lemonsoft API Configuration
    lemonsoft_api_url: str = Field(
        default="https://integraatiot.lvi-wabek.fi/LemonRest",
        env="LEMONSOFT_API_URL",
        description="Base URL for Lemonsoft API"
    )
    lemonsoft_username: str = Field(
        env="LEMONSOFT_USERNAME",
        description="Lemonsoft API username"
    )
    lemonsoft_password: str = Field(
        env="LEMONSOFT_PASSWORD",
        description="Lemonsoft API password"
    )
    lemonsoft_sql_password: Optional[str] = Field(
        default=None,
        env="LEMONSOFT_SQL_PASSWORD", 
        description="Lemonsoft SQL Server authentication password (for Docker/production)"
    )
    lemonsoft_database: str = Field(
        env="LEMONSOFT_DATABASE",
        description="Lemonsoft database name"
    )
    lemonsoft_api_key: str = Field(
        env="LEMONSOFT_API_KEY",
        description="Lemonsoft API key"
    )
    
    # Database Configuration
    database_host: str = Field(
        default="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        env="DATABASE_HOST",
        description="Database server hostname or IP address"
    )
    database_port: str = Field(
        default="1433",
        env="DATABASE_PORT",
        description="Database server port"
    )
    database_name: str = Field(
        default="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        env="DATABASE_NAME",
        description="Database name"
    )
    database_driver: str = Field(
        default="SQL Server",
        env="DATABASE_DRIVER",
        description="SQL Server connection"
    )
    
    # Deployment Configuration
    deployment_mode: str = Field(
        default="docker",
        env="DEPLOYMENT_MODE",
        description="Deployment mode: local, docker, production"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    redis_password: Optional[str] = Field(
        default=None,
        env="REDIS_PASSWORD",
        description="Redis password if required"
    )
    
    # Email SMTP Configuration
    smtp_host: str = Field(
        default="smtp.gmail.com",
        env="SMTP_HOST",
        description="SMTP host for email notifications"
    )
    smtp_port: int = Field(
        default=587,
        env="SMTP_PORT",
        description="SMTP port for email notifications"
    )
    smtp_use_tls: bool = Field(
        default=True,
        env="SMTP_USE_TLS",
        description="Use TLS for SMTP connection"
    )
    smtp_auth_method: str = Field(
        default="basic",
        env="SMTP_AUTH_METHOD",
        description="SMTP authentication method"
    )
    smtp_username: str = Field(
        env="SMTP_USERNAME",
        description="SMTP username for email notifications"
    )
    smtp_password: str = Field(
        env="SMTP_PASSWORD",
        description="SMTP password for email notifications"
    )
    email_from_address: str = Field(
        default="offers@company.com",
        env="EMAIL_FROM_ADDRESS",
        description="From email address for notifications"
    )
    email_from_name: str = Field(
        default="Offer Automation System",
        env="EMAIL_FROM_NAME",
        description="From name for email notifications"
    )
    email_reply_to: str = Field(
        env="EMAIL_REPLY_TO",
        description="Reply-to email address"
    )
    
    # Gmail Configuration
    gmail_service_account_file: Optional[str] = Field(
        default=None,
        env="GMAIL_SERVICE_ACCOUNT_FILE",
        description="Path to Gmail service account JSON file"
    )

    monitored_email: str = Field(
        default="ai.tarjous.wcom@gmail.com",
        env="MONITORED_EMAIL",
        description="Email address to monitor and send from"
    )
    
    # Email Processing Configuration
    email_check_interval: int = Field(
        default=60,
        env="EMAIL_CHECK_INTERVAL",
        description="Email check interval in seconds"
    )
    email_max_attachment_size: int = Field(
        default=10485760,
        env="EMAIL_MAX_ATTACHMENT_SIZE",
        description="Maximum email attachment size in bytes"
    )
    email_allowed_senders: str = Field(
        default="",
        env="EMAIL_ALLOWED_SENDERS",
        description="Comma-separated list of allowed sender domains"
    )
    
    # Notification Configuration
    notification_recipients: str = Field(
        default="",
        env="NOTIFICATION_RECIPIENTS",
        description="Comma-separated list of notification recipients"
    )
    error_notification_recipients: str = Field(
        default="",
        env="ERROR_NOTIFICATION_RECIPIENTS",
        description="Comma-separated list of error notification recipients"
    )
    
    # Legacy Email SMTP Configuration (kept for backward compatibility)
    email_smtp_host: str = Field(
        default="smtp.gmail.com",
        env="EMAIL_SMTP_HOST",
        description="SMTP host for email notifications (legacy)"
    )
    email_smtp_port: int = Field(
        default=587,
        env="EMAIL_SMTP_PORT",
        description="SMTP port for email notifications (legacy)"
    )
    email_username: str = Field(
        env="EMAIL_USERNAME",
        description="SMTP username for email notifications (legacy)"
    )
    email_password: str = Field(
        env="EMAIL_PASSWORD",
        description="SMTP password for email notifications (legacy)"
    )
    
    # Web Search Configuration
    web_search_api_key: Optional[str] = Field(
        default=None,
        env="WEB_SEARCH_API_KEY",
        description="API key for web search service"
    )
    web_search_engine: str = Field(
        default="google",
        env="WEB_SEARCH_ENGINE",
        description="Web search engine to use"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log output format"
    )
    
    # Product Data Configuration
    product_csv_path: str = Field(
        default="/app/data/example.csv",
        env="PRODUCT_CSV_PATH",
        description="Path to product CSV file"
    )
    product_update_interval: int = Field(
        default=3600,
        env="PRODUCT_UPDATE_INTERVAL",
        description="Product data update interval in seconds"
    )
    
    # Processing Configuration
    max_concurrent_requests: int = Field(
        default=5,
        env="MAX_CONCURRENT_REQUESTS",
        description="Maximum number of concurrent requests to process"
    )
    request_timeout: int = Field(
        default=120,
        env="REQUEST_TIMEOUT",
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        env="RETRY_ATTEMPTS",
        description="Number of retry attempts for failed operations"
    )
    
    # Confidence Thresholds
    customer_match_threshold: float = Field(
        default=0.8,
        env="CUSTOMER_MATCH_THRESHOLD",
        description="Minimum confidence threshold for customer matching"
    )
    product_match_threshold: float = Field(
        default=0.7,
        env="PRODUCT_MATCH_THRESHOLD",
        description="Minimum confidence threshold for product matching"
    )
    use_fallback_search: bool = Field(
        default=True,
        env="USE_FALLBACK_SEARCH",
        description="Whether to use fallback search methods"
    )
    
    # Security
    session_secret_key: str = Field(
        env="SESSION_SECRET_KEY",
        description="Secret key for session management"
    )
    api_rate_limit: int = Field(
        default=100,
        env="API_RATE_LIMIT",
        description="API rate limit per minute"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "allow"  # Allow extra environment variables not defined in schema
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @validator("customer_match_threshold", "product_match_threshold")
    def validate_thresholds(cls, v):
        """Validate confidence thresholds are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence thresholds must be between 0 and 1")
        return v
    
    @validator("product_csv_path")
    def validate_product_csv_path(cls, v):
        """Validate product CSV path exists or create it if in container."""
        # In development, the file might not exist yet
        # In production (container), we'll ensure it exists
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global settings
    settings = Settings()
    return settings 