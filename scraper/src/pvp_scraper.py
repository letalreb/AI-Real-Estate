"""
Main scraper for pvp.giustizia.it auction portal.
Uses the JSON API endpoint for efficient data retrieval.
"""
import asyncio
import aiohttp
import structlog
from typing import List, Dict, Any
from datetime import datetime
import json

from .config import settings
from .rate_limiter import RateLimiter
from .publisher import publish_auction_data

logger = structlog.get_logger()

class PVPScraper:
    """Scraper for pvp.giustizia.it portal using JSON API."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=30,
            delay_ms=settings.SCRAPER_DELAY_MS
        )
        self.base_url = "https://pvp.giustizia.it"
        self.api_url = f"{self.base_url}/ric-496b258c-986a1b71/ric-ms/ricerca/vendite"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=settings.SCRAPER_TIMEOUT_SECONDS)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en,it;q=0.9,en-US;q=0.8,it-IT;q=0.7",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/pvp/it/lista_annunci.page",
        }
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_api_data(self, page: int = 0, size: int = 12) -> Dict[str, Any]:
        """Fetch auction data from JSON API."""
        await self.rate_limiter.wait(self.base_url)
        
        url = f"{self.api_url}?language=it&page={page}&size={size}&sort=dataOraVendita,asc&sort=citta,asc"
        
        payload = {
            "tipoLotto": "IMMOBILI",
            "categoriaBene": [],
            "flagRicerca": 0,
            "coordIndirizzo": "",
            "raggioIndirizzo": "25"
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info("api_fetch_success", page=page, status=response.status)
                return data
        except Exception as e:
            logger.error("api_fetch_failed", url=url, error=str(e))
            raise
    
    async def scrape_auction_list(self, page: int = 0) -> List[Dict[str, Any]]:
        """Scrape auction list using API."""
        try:
            api_response = await self.fetch_api_data(page=page, size=12)
            
            auctions = []
            # API response structure: {"body": {"content": [...]}}
            body = api_response.get('body', {})
            content = body.get('content', [])
            
            for item in content:
                try:
                    indirizzo = item.get('indirizzo', {})
                    coordinate = indirizzo.get('coordinate', {})
                    
                    # Convert auction_round to integer or None
                    procedura = item.get('procedura')
                    auction_round = None
                    if procedura:
                        try:
                            auction_round = int(procedura)
                        except (ValueError, TypeError):
                            auction_round = None
                    
                    auction_data = {
                        'external_id': str(item.get('id', '')),
                        'title': item.get('descLotto', ''),
                        'url': f"{self.base_url}/pvp/it/dettaglio.page?idAnnuncio={item.get('id', '')}",
                        'property_type': ','.join(item.get('categoriaBene', [])) if isinstance(item.get('categoriaBene'), list) else item.get('categoriaBene', ''),
                        'city': indirizzo.get('citta', ''),
                        'province': indirizzo.get('provincia', ''),
                        'address': indirizzo.get('via', ''),
                        'latitude': coordinate.get('latitudine'),
                        'longitude': coordinate.get('longitudine'),
                        'price_text': str(item.get('prezzoBaseAsta', '')),
                        'base_price': float(item.get('prezzoBaseAsta', 0)) if item.get('prezzoBaseAsta') else None,
                        'auction_date': item.get('dataOraVendita', ''),
                        'auction_round': auction_round,
                        'court': item.get('tribunale', ''),
                        'scraped_at': datetime.utcnow().isoformat(),
                        'raw_data': item
                    }
                    
                    if auction_data['external_id']:
                        auctions.append(auction_data)
                
                except Exception as e:
                    logger.warning("parse_item_failed", item_id=item.get('id'), error=str(e))
                    continue
            
            total_elements = body.get('totalElements', len(content))
            logger.info("scraped_auction_list", page=page, count=len(auctions), total=total_elements)
            return auctions
            
        except Exception as e:
            logger.error("scrape_page_failed", page=page, error=str(e))
            return []
    
    async def run(self, max_pages: int = 5):
        """Main scraping loop using API."""
        logger.info("starting_scraper", max_pages=max_pages)
        
        total_auctions = 0
        
        for page in range(0, max_pages):
            try:
                # Fetch auctions from API
                auctions = await self.scrape_auction_list(page)
                
                if not auctions:
                    logger.info("no_more_auctions", page=page)
                    break
                
                # Publish each auction to backend
                for auction in auctions:
                    try:
                        await publish_auction_data(auction)
                        total_auctions += 1
                        logger.debug("published_auction", auction_id=auction.get('external_id'))
                    except Exception as e:
                        logger.error("publish_failed", auction_id=auction.get('external_id'), error=str(e))
                
                # Polite delay between pages
                await asyncio.sleep(settings.SCRAPER_DELAY_MS / 1000.0)
            
            except Exception as e:
                logger.error("scraping_error", page=page, error=str(e))
                continue
        
        logger.info("scraping_completed", total_auctions=total_auctions)


async def main():
    """Entry point for scraper."""
    async with PVPScraper() as scraper:
        await scraper.run(max_pages=100)  # Increased from 10 to 100 to get more auctions


if __name__ == "__main__":
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    asyncio.run(main())
