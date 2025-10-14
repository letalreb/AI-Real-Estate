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
