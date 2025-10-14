"""
Configuration management using Pydantic Settings.
Loads settings from environment variables and .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "auction_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "auction_db"
    DATABASE_URL: Optional[str] = None
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RATE_LIMIT: int = 100
    CORS_ORIGINS: str = "http://localhost:3000"
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    
    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_URL: Optional[str] = None
    QDRANT_COLLECTION: str = "auctions"
    
    # NLP Service
    NLP_SERVICE_HOST: str = "nlp-service"
    NLP_SERVICE_PORT: int = 8001
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Admin
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str
    
    # Config file
    RANKING_CONFIG_PATH: str = "/app/config/config.yaml"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_database_url(self) -> str:
        """Get database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_redis_url(self) -> str:
        """Get Redis URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    def get_qdrant_url(self) -> str:
        """Get Qdrant URL."""
        if self.QDRANT_URL:
            return self.QDRANT_URL
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
    
    def get_nlp_service_url(self) -> str:
        """Get NLP service URL."""
        return f"http://{self.NLP_SERVICE_HOST}:{self.NLP_SERVICE_PORT}"


# Global settings instance
settings = Settings()
