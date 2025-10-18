"""
Main scraper for pvp.giustizia.it auction portal.
Uses the JSON API endpoint with anti-ban measures.
"""
import asyncio
import aiohttp
import structlog
from typing import List, Dict, Any
from datetime import datetime
import json
import random

from .config import settings
from .rate_limiter import RateLimiter
from .publisher import publish_auction_data
from .user_agents import get_browser_headers

logger = structlog.get_logger()

class PVPScraper:
    """Scraper for pvp.giustizia.it portal with anti-ban measures."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=6,  # Ridotto drasticamente: max 6 req/min = 1 ogni 10 sec
            delay_ms=settings.SCRAPER_DELAY_MS
        )
        self.base_url = "https://pvp.giustizia.it"
        self.api_url = f"{self.base_url}/ric-496b258c-986a1b71/ric-ms/ricerca/vendite"
        self.session = None
        self.request_count = 0
    
    async def __aenter__(self):
        """Async context manager entry with rotating headers."""
        timeout = aiohttp.ClientTimeout(total=settings.SCRAPER_TIMEOUT_SECONDS)
        
        # Use rotating browser headers
        headers = get_browser_headers(referer=f"{self.base_url}/pvp/it/lista_annunci.page")
        headers["Origin"] = self.base_url
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        logger.info("session_started", user_agent=headers.get("User-Agent", "unknown")[:50])
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_api_data(self, page: int = 0, size: int = 12) -> Dict[str, Any]:
        """Fetch auction data from JSON API with random delays."""
        # Random delay between requests (5-15 seconds) per apparire più umano
        random_delay = settings.get_random_delay_ms() / 1000.0
        logger.info("waiting_before_request", delay_seconds=round(random_delay, 1))
        await asyncio.sleep(random_delay)
        
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
            self.request_count += 1
            async with self.session.post(url, json=payload) as response:
                if response.status == 403:
                    logger.error("access_forbidden", status=403, message="Possibile ban dal sito")
                    raise Exception("403 Forbidden - Sito potrebbe aver bannato questo IP")
                elif response.status == 429:
                    logger.error("rate_limited", status=429, message="Too many requests")
                    raise Exception("429 Too Many Requests - Rate limit superato")
                
                response.raise_for_status()
                data = await response.json()
                logger.info("api_fetch_success", 
                          page=page, 
                          status=response.status,
                          total_requests=self.request_count)
                return data
        except aiohttp.ClientResponseError as e:
            logger.error("api_fetch_failed", 
                        url=url, 
                        status=e.status if hasattr(e, 'status') else 'unknown',
                        error=str(e))
            raise
        except Exception as e:
            logger.error("api_fetch_failed", url=url, error=str(e))
            raise
    
    async def scrape_auction_list(self, page: int = 0) -> List[Dict[str, Any]]:
        """
        Scrape auction list using API.
        Returns list of auctions, or raises exception if API call fails.
        """
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
    
    async def run(self, max_pages: int = None):
        """Main scraping loop with anti-ban measures."""
        if max_pages is None:
            max_pages = settings.SCRAPER_MAX_PAGES_PER_RUN
        
        logger.info("starting_scraper", 
                   max_pages=max_pages,
                   delay_range=f"{settings.SCRAPER_MIN_DELAY_MS}-{settings.SCRAPER_MAX_DELAY_MS}ms")
        
        total_auctions = 0
        consecutive_failures = 0
        max_consecutive_failures = 2  # Ridotto a 2 per fermarsi prima
        
        for page in range(0, max_pages):
            try:
                # Fetch auctions from API
                auctions = await self.scrape_auction_list(page)
                
                if not auctions:
                    consecutive_failures += 1
                    logger.warning("empty_page_result", 
                                 page=page, 
                                 consecutive_failures=consecutive_failures)
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("too_many_consecutive_failures", 
                                   consecutive_failures=consecutive_failures,
                                   reason="stopping_to_avoid_detection")
                        break
                    
                    # Wait even longer after empty pages
                    pause_time = settings.SCRAPER_PAUSE_AFTER_ERROR
                    logger.info("pausing_after_empty_page", seconds=pause_time)
                    await asyncio.sleep(pause_time)
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # Publish each auction to backend
                for auction in auctions:
                    try:
                        await publish_auction_data(auction)
                        total_auctions += 1
                        logger.debug("published_auction", auction_id=auction.get('external_id'))
                    except Exception as e:
                        logger.error("publish_failed", 
                                   auction_id=auction.get('external_id'), 
                                   error=str(e))
                
                logger.info("page_completed", 
                          page=page, 
                          auctions_on_page=len(auctions),
                          total_published=total_auctions)
            
            except Exception as e:
                consecutive_failures += 1
                error_msg = str(e)
                
                # Check if we got banned
                if "403" in error_msg or "429" in error_msg or "Forbidden" in error_msg:
                    logger.critical("banned_or_rate_limited",
                                  error=error_msg,
                                  page=page,
                                  total_requests=self.request_count,
                                  suggestion="Aumentare delay o cambiare IP")
                    break
                
                logger.error("scraping_error", 
                           page=page, 
                           error=error_msg, 
                           consecutive_failures=consecutive_failures)
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error("too_many_consecutive_errors", 
                               consecutive_failures=consecutive_failures,
                               reason="stopping_to_avoid_ban")
                    break
                
                # Exponential backoff con pausa più lunga
                wait_time = settings.SCRAPER_PAUSE_AFTER_ERROR * (2 ** (consecutive_failures - 1))
                logger.info("backing_off_after_error", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
        
        logger.info("scraping_completed", 
                   total_auctions=total_auctions,
                   pages_scraped=page + 1,
                   total_requests=self.request_count,
                   final_consecutive_failures=consecutive_failures)


async def main():
    """Entry point for scraper with conservative limits."""
    logger.info("scraper_starting", 
               mode="conservative",
               note="Using long delays and low request rate to avoid bans")
    
    async with PVPScraper() as scraper:
        # Limita a 3 pagine per run per evitare ban
        await scraper.run(max_pages=3)
    
    logger.info("scraper_session_complete",
               next_run=f"in {settings.SCRAPER_RUN_INTERVAL_MINUTES} minutes")


if __name__ == "__main__":
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    asyncio.run(main())
