"""Scraper configuration."""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    SCRAPER_CONCURRENCY: int = 2
    SCRAPER_DELAY_MS: int = 1000
    SCRAPER_TIMEOUT_SECONDS: int = 30
    SCRAPER_RETRY_ATTEMPTS: int = 3
    RESPECT_ROBOTS_TXT: bool = True
    SCRAPER_USER_AGENT: str = "AI-RealEstate-Bot/1.0"
    SCRAPER_TARGETS: str = "https://pvp.giustizia.it/pvp/"
    
    REDIS_URL: str = "redis://redis:6379/0"
    NLP_SERVICE_URL: str = "http://nlp-service:8001"
    BACKEND_API_URL: str = "http://backend:8000"
    
    class Config:
        env_file = ".env"

settings = Settings()
