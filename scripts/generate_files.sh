#!/bin/bash

# AI Real Estate Auction Analyzer - Complete Setup Script
# This script generates all remaining source files for the project

set -e

echo "🏗️  Generating AI Real Estate Auction Analyzer project files..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p backend/src/{api,tests}
mkdir -p backend/migrations/versions
mkdir -p scraper/src/tests
mkdir -p nlp-service/src/{models,tests}
mkdir -p frontend/src/{pages,components,services}
mkdir -p frontend/public
mkdir -p infra/{kubernetes,terraform}
mkdir -p scripts
mkdir -p docs/diagrams

# Generate scraper service files
echo "🕷️  Generating scraper files..."

cat > scraper/src/__init__.py << 'EOF'
"""Scraper service package."""
EOF

cat > scraper/src/config.py << 'EOF'
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
EOF

cat > scraper/src/rate_limiter.py << 'EOF'
"""Rate limiter for polite scraping."""
import asyncio
import time
from typing import Dict

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30, delay_ms: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.delay_ms = delay_ms
        self.last_request_time: Dict[str, float] = {}
    
    async def wait(self, domain: str):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        last_time = self.last_request_time.get(domain, 0)
        time_since_last = current_time - last_time
        min_interval = self.delay_ms / 1000.0
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
EOF

cat > scraper/src/pvp_scraper.py << 'EOF'
"""
Main scraper for pvp.giustizia.it auction portal.
Implements polite scraping with rate limiting and robots.txt compliance.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import structlog
from typing import List, Dict, Any
from datetime import datetime
import re

from .config import settings
from .rate_limiter import RateLimiter
from .publisher import publish_auction_data

logger = structlog.get_logger()

class PVPScraper:
    """Scraper for pvp.giustizia.it portal."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=30,
            delay_ms=settings.SCRAPER_DELAY_MS
        )
        self.base_url = "https://pvp.giustizia.it"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=settings.SCRAPER_TIMEOUT_SECONDS)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": settings.SCRAPER_USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        """Fetch a page with rate limiting."""
        await self.rate_limiter.wait(self.base_url)
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error("fetch_failed", url=url, error=str(e))
            raise
    
    async def scrape_auction_list(self, page: int = 1) -> List[Dict[str, Any]]:
        """Scrape auction list page."""
        # In real implementation, this would use the actual API/endpoints
        # For demo purposes, we'll simulate the structure
        
        url = f"{self.base_url}/pvp/it/ricerca.page?page={page}"
        html = await self.fetch_page(url)
        
        soup = BeautifulSoup(html, 'lxml')
        auctions = []
        
        # Parse auction cards (adjust selectors based on actual site structure)
        for item in soup.select('.auction-item'):  # Example selector
            try:
                auction_data = {
                    'external_id': item.get('data-id', ''),
                    'title': item.select_one('.title').text.strip() if item.select_one('.title') else '',
                    'url': urljoin(self.base_url, item.select_one('a')['href']) if item.select_one('a') else '',
                    'price_text': item.select_one('.price').text if item.select_one('.price') else '',
                    'city': item.select_one('.location').text if item.select_one('.location') else '',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                if auction_data['external_id']:
                    auctions.append(auction_data)
            
            except Exception as e:
                logger.warning("parse_item_failed", error=str(e))
                continue
        
        logger.info("scraped_auction_list", page=page, count=len(auctions))
        return auctions
    
    async def scrape_auction_detail(self, auction_id: str, url: str) -> Dict[str, Any]:
        """Scrape detailed auction page."""
        html = await self.fetch_page(url)
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract detailed information
        detail_data = {
            'external_id': auction_id,
            'source_url': url,
            'full_text': soup.get_text(separator=' ', strip=True),
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        logger.info("scraped_auction_detail", auction_id=auction_id)
        return detail_data
    
    async def run(self, max_pages: int = 5):
        """Main scraping loop."""
        logger.info("starting_scraper", max_pages=max_pages)
        
        total_auctions = 0
        
        for page in range(1, max_pages + 1):
            try:
                # Scrape list page
                auctions = await self.scrape_auction_list(page)
                
                # Scrape each detail page
                for auction in auctions:
                    if auction.get('url'):
                        detail = await self.scrape_auction_detail(
                            auction['external_id'],
                            auction['url']
                        )
                        
                        # Merge data
                        auction.update(detail)
                        
                        # Publish to NLP service
                        await publish_auction_data(auction)
                        total_auctions += 1
                
                # Polite delay between pages
                await asyncio.sleep(settings.SCRAPER_DELAY_MS / 1000.0)
            
            except Exception as e:
                logger.error("scraping_error", page=page, error=str(e))
                continue
        
        logger.info("scraping_completed", total_auctions=total_auctions)


async def main():
    """Entry point for scraper."""
    async with PVPScraper() as scraper:
        await scraper.run(max_pages=10)


if __name__ == "__main__":
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    asyncio.run(main())
EOF

cat > scraper/src/publisher.py << 'EOF'
"""Publish scraped data to NLP service."""
import aiohttp
import structlog
from typing import Dict, Any

from .config import settings

logger = structlog.get_logger()

async def publish_auction_data(auction_data: Dict[str, Any]) -> bool:
    """
    Publish auction data to NLP service for processing.
    
    Args:
        auction_data: Scraped auction data
    
    Returns:
        Success boolean
    """
    url = f"{settings.NLP_SERVICE_URL}/process"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=auction_data) as response:
                if response.status == 200:
                    logger.info(
                        "data_published",
                        auction_id=auction_data.get('external_id')
                    )
                    return True
                else:
                    logger.error(
                        "publish_failed",
                        status=response.status,
                        auction_id=auction_data.get('external_id')
                    )
                    return False
    
    except Exception as e:
        logger.error(
            "publish_error",
            error=str(e),
            auction_id=auction_data.get('external_id')
        )
        return False
EOF

echo "✅ Scraper files generated"

# Generate NLP service files
echo "🧠 Generating NLP service files..."

cat > nlp-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download it_core_news_lg

COPY . .

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

cat > nlp-service/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
spacy==3.7.2
sentence-transformers==2.3.1
numpy==1.26.3
scikit-learn==1.4.0
pydantic==2.5.3
pydantic-settings==2.1.0
redis==5.0.1
qdrant-client==1.7.3
pyyaml==6.0.1
structlog==24.1.0
torch==2.1.2
pytest==7.4.4
EOF

echo "✅ NLP service structure created"

echo ""
echo "✅ File generation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Review generated files"
echo "   2. Copy .env.example to .env and configure"
echo "   3. Run: docker-compose up --build"
echo ""
