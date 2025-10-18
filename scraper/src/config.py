"""Scraper configuration."""
from pydantic_settings import BaseSettings
from typing import List
import random

class Settings(BaseSettings):
    SCRAPER_CONCURRENCY: int = 1  # Ridotto a 1 per evitare ban
    SCRAPER_DELAY_MS: int = 8000  # Aumentato a 8 secondi tra richieste
    SCRAPER_MIN_DELAY_MS: int = 5000  # Minimo 5 secondi
    SCRAPER_MAX_DELAY_MS: int = 15000  # Massimo 15 secondi
    SCRAPER_TIMEOUT_SECONDS: int = 45  # Aumentato timeout
    SCRAPER_RETRY_ATTEMPTS: int = 2  # Ridotto tentativi per evitare ban
    RESPECT_ROBOTS_TXT: bool = True
    SCRAPER_USER_AGENT: str = "AI-RealEstate-Bot/1.0"
    SCRAPER_TARGETS: str = "https://pvp.giustizia.it/pvp/"
    
    # Anti-ban settings
    SCRAPER_MAX_PAGES_PER_RUN: int = 5  # Massimo 5 pagine per run
    SCRAPER_PAUSE_AFTER_ERROR: int = 60  # Pausa di 60 secondi dopo errore
    SCRAPER_RUN_INTERVAL_MINUTES: int = 30  # Run ogni 30 minuti
    
    REDIS_URL: str = "redis://redis:6379/0"
    NLP_SERVICE_URL: str = "http://nlp-service:8001"
    BACKEND_API_URL: str = "http://backend:8000"
    
    class Config:
        env_file = ".env"
    
    def get_random_delay_ms(self) -> int:
        """Get random delay between min and max to appear more human."""
        return random.randint(self.SCRAPER_MIN_DELAY_MS, self.SCRAPER_MAX_DELAY_MS)

settings = Settings()
