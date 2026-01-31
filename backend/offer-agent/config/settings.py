"""
Application configuration settings using Pydantic.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Gmail API Configuration
    gmail_credentials_file: str = Field(..., description="Path to Gmail API credentials JSON file")
    gmail_token_file: str = Field(default="token.json", description="Path to Gmail API token file")
    gmail_scopes: list = Field(default=["https://www.googleapis.com/auth/gmail.readonly"], description="Gmail API scopes")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for GPT and embedding models")
    openai_model: str = Field(default="gpt-4", description="Default OpenAI model for chat completion")
    openai_embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    openai_max_tokens: int = Field(default=4000, description="Maximum tokens for OpenAI responses")
    openai_temperature: float = Field(default=0.1, description="Temperature for OpenAI models")
    
    # Qdrant Vector Database Configuration
    qdrant_host: str = Field(default="localhost", description="Qdrant server host")
    qdrant_port: int = Field(default=6333, description="Qdrant server port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key (if required)")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis server host for caching")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_password: Optional[str] = Field(default=None, description="Redis password (if required)")
    redis_db: int = Field(default=0, description="Redis database number")
    
    # ERP Integration
    erp_api_key: str = Field(..., description="ERP API key")
    erp_api_secret: str = Field(..., description="ERP API secret")
    erp_base_url: str = Field(..., description="ERP API base URL")
    erp_company_id: str = Field(..., description="ERP company ID")
    erp_user_id: str = Field(..., description="ERP user ID for API operations")
    
    # Database Configuration (PostgreSQL for audit logs)
    database_url: str = Field(..., description="PostgreSQL database URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    
    # Webhook Configuration
    webhook_secret: str = Field(..., description="Webhook secret for validation")
    webhook_port: int = Field(default=8000, description="Webhook server port")
    
    # Email Configuration (for notifications)
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # File Storage
    temp_dir: str = Field(default="./temp", description="Temporary files directory")
    upload_dir: str = Field(default="./uploads", description="File uploads directory")
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 