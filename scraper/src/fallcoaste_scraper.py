"""
Scraper for www.fallcoaste.it auction portal.
Extracts Italian judicial auction data and normalizes it.
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import random

from .config import settings
from .rate_limiter import RateLimiter
from .publisher import publish_auction_data
from .matching_utils import find_best_match, enrich_pvp_auction

logger = structlog.get_logger()


async def fetch_pvp_auctions_from_backend() -> List[Dict[str, Any]]:
    """Fetch all PVP auctions from backend for matching."""
    try:
        async with aiohttp.ClientSession() as session:
            # Fetch from backend API
            url = f"{settings.BACKEND_URL}/api/v1/auctions"
            params = {
                'limit': 10000,  # Get all auctions
                'source': 'pvp'  # Only PVP auctions (source of truth)
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    auctions = data.get('items', [])
                    logger.info("fetched_pvp_auctions_for_matching", count=len(auctions))
                    return auctions
                else:
                    logger.error("fetch_pvp_auctions_failed", status=response.status)
                    return []
    except Exception as e:
        logger.error("fetch_pvp_auctions_error", error=str(e))
        return []

class FallcoasteScraper:
    """Scraper for www.fallcoaste.it portal with resilience."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(
            requests_per_minute=15,  # Conservativo per rispettare il server
            delay_ms=settings.SCRAPER_DELAY_MS
        )
        self.base_url = "https://www.fallcoaste.it"
        self.search_url = f"{self.base_url}/ricerca.html"
        self.session = None
        self.max_retries = 5
        self.base_backoff = 2
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(
            total=60,
            connect=10,
            sock_read=30
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        
        connector = aiohttp.TCPConnector(
            limit=2,
            limit_per_host=1,
            ttl_dns_cache=300,
            ssl=False
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=connector
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, page: int = 1) -> Optional[str]:
        """
        Fetch HTML page from Fallcoaste with retry logic.
        
        Args:
            page: Page number to fetch
            
        Returns:
            HTML content or None if all retries failed
        """
        await self.rate_limiter.wait(self.base_url)
        
        params = {
            "filter": "macro|527^input_categoria|Beni Immobili^ubicazione_dst|50^stato|1",
            "page": str(page)
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "fallcoaste_request_attempt",
                    page=page,
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                
                if attempt > 0:
                    jitter = random.uniform(0, 1)
                    await asyncio.sleep(jitter)
                
                async with self.session.get(self.search_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        logger.info("fallcoaste_fetch_success", page=page, attempt=attempt + 1)
                        return html
                    elif response.status == 429:
                        wait_time = self.base_backoff * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            "fallcoaste_rate_limited",
                            page=page,
                            wait_time=wait_time
                        )
                        await asyncio.sleep(wait_time)
                    elif response.status >= 500:
                        wait_time = self.base_backoff * (2 ** attempt)
                        logger.warning(
                            "fallcoaste_server_error",
                            page=page,
                            status=response.status,
                            wait_time=wait_time
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error("fallcoaste_unexpected_status", page=page, status=response.status)
                        await asyncio.sleep(self.base_backoff * (2 ** attempt))
                        
            except asyncio.TimeoutError:
                wait_time = self.base_backoff * (2 ** attempt) + random.uniform(0, 2)
                logger.warning("fallcoaste_timeout", page=page, wait_time=wait_time)
                await asyncio.sleep(wait_time)
                
            except aiohttp.ClientError as e:
                wait_time = self.base_backoff * (2 ** attempt) + random.uniform(0, 2)
                logger.warning("fallcoaste_client_error", page=page, error=str(e), wait_time=wait_time)
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error("fallcoaste_unexpected_error", page=page, error=str(e))
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_backoff * (2 ** attempt))
        
        logger.error("fallcoaste_fetch_failed_all_retries", page=page)
        return None
    
    async def fetch_detail_page(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse detail page for an auction.
        
        Args:
            detail_url: URL of the auction detail page
            
        Returns:
            Dictionary with detailed auction data or None
        """
        await self.rate_limiter.wait(self.base_url)
        
        try:
            async with self.session.get(detail_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.parse_detail_page(html)
                else:
                    logger.warning("fallcoaste_detail_fetch_failed", url=detail_url, status=response.status)
                    return None
        except Exception as e:
            logger.error("fallcoaste_detail_fetch_error", url=detail_url, error=str(e))
            return None
    
    def parse_detail_page(self, html: str) -> Optional[Dict[str, Any]]:
        """Parse auction detail page to extract all fields."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            details = {}
            
            # Trova tutti i campi strutturati
            for row in soup.find_all(['dt', 'dd']):
                text = row.get_text(strip=True)
                if ':' in text:
                    key, value = text.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    details[key] = value
            
            return details
        except Exception as e:
            logger.error("fallcoaste_detail_parse_error", error=str(e))
            return None
    
    def extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract auction ID from URL."""
        match = re.search(r'-(\d+)\.html', url)
        if match:
            return f"fallcoaste_{match.group(1)}"
        return None
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        try:
            # Rimuovi simboli e converti
            price_clean = re.sub(r'[€.,\s]', '', price_text)
            price_clean = price_clean.replace(',', '.')
            return float(price_clean) if price_clean else None
        except:
            return None
    
    def extract_pvp_id(self, text: str) -> Optional[str]:
        """Extract ID inserzione PVP from text or link."""
        match = re.search(r'idAnnuncio[=:](\d+)', text)
        if match:
            return match.group(1)
        return None
    
    async def parse_auction_list(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML to extract auction listings."""
        auctions = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Trova tutti i risultati (adatta il selettore alla struttura reale)
            auction_items = soup.find_all('div', class_=re.compile(r'result|auction|item|card'))
            
            if not auction_items:
                # Fallback: cerca link con pattern comune
                auction_items = soup.find_all('a', href=re.compile(r'(avviso-vendita|vendita)/'))
            
            for item in auction_items:
                try:
                    # Estrai link dettaglio
                    link_tag = item.find('a', href=True) if item.name != 'a' else item
                    if not link_tag:
                        continue
                    
                    detail_url = link_tag['href']
                    if not detail_url.startswith('http'):
                        detail_url = f"{self.base_url}{detail_url}"
                    
                    # External ID univoco
                    external_id = self.extract_id_from_url(detail_url)
                    if not external_id:
                        continue
                    
                    # Estrai titolo
                    title_tag = item.find(['h2', 'h3', 'h4', 'a'])
                    title = title_tag.get_text(strip=True) if title_tag else "Immobile all'asta"
                    
                    # Estrai prezzo base
                    price_text = ""
                    price_tag = item.find(text=re.compile(r'Prezzo base|€'))
                    if price_tag:
                        price_text = price_tag.strip()
                        base_price = self.extract_price(price_text)
                    else:
                        base_price = None
                    
                    # Estrai data vendita/inizio
                    date_text = ""
                    date_tag = item.find(text=re.compile(r'Inizio|Termine|Data'))
                    if date_tag:
                        date_text = date_tag.strip()
                    
                    # Estrai tribunale
                    tribunal_text = ""
                    tribunal_tag = item.find(text=re.compile(r'Tribunale'))
                    if tribunal_tag:
                        tribunal_text = tribunal_tag.strip()
                    
                    # Fetch detail page per dati completi
                    detail_data = await self.fetch_detail_page(detail_url)
                    
                    # Combina dati base con dettagli
                    auction_data = {
                        'external_id': external_id,
                        'title': title[:500],  # Limita lunghezza
                        'url': detail_url,
                        'source': 'fallcoaste',
                        'base_price': base_price,
                        'price_text': price_text,
                        'auction_date': date_text,
                        'court': tribunal_text,
                        'scraped_at': datetime.utcnow().isoformat(),
                    }
                    
                    # Aggiungi dettagli se disponibili
                    if detail_data:
                        # Procedura n.
                        if 'Procedura n' in detail_data:
                            auction_data['case_number'] = detail_data['Procedura n']
                        
                        # Tipo procedura
                        if 'Tipo procedura' in detail_data:
                            auction_data['procedure_type'] = detail_data['Tipo procedura']
                        
                        # Tribunale
                        if 'Tribunale' in detail_data:
                            auction_data['court'] = detail_data['Tribunale']
                        
                        # Referente procedura
                        if 'Referente procedura' in detail_data:
                            auction_data['referent'] = detail_data['Referente procedura']
                        
                        # Termine presentazione offerte
                        if 'Termine presentazione offerte' in detail_data:
                            auction_data['offer_deadline'] = detail_data['Termine presentazione offerte']
                        
                        # Termine visita
                        if 'Termine visita' in detail_data:
                            auction_data['visit_deadline'] = detail_data['Termine visita']
                        
                        # Data vendita
                        if 'Data vendita' in detail_data:
                            auction_data['auction_date'] = detail_data['Data vendita']
                        
                        # ID inserzione PVP
                        pvp_id = None
                        if 'ID inserzione PVP' in detail_data:
                            pvp_id = detail_data['ID inserzione PVP']
                        elif 'Link inserzione ministeriale' in detail_data:
                            pvp_id = self.extract_pvp_id(detail_data['Link inserzione ministeriale'])
                        
                        if pvp_id:
                            auction_data['pvp_id'] = pvp_id
                            # Genera link PVP se disponibile
                            auction_data['pvp_url'] = f"https://pvp.giustizia.it/pvp/it/dettaglio.page?idAnnuncio={pvp_id}"
                        
                        # Codice vendita
                        if 'Codice vendita' in detail_data:
                            auction_data['sale_code'] = detail_data['Codice vendita']
                        
                        # Data pubblicazione
                        if 'Data pubblicazione' in detail_data:
                            auction_data['publication_date'] = detail_data['Data pubblicazione']
                        
                        # Cauzione minima
                        if 'Cauzione minima' in detail_data:
                            auction_data['minimum_deposit'] = self.extract_price(detail_data['Cauzione minima'])
                        
                        # Annotazioni PVP
                        if 'Annotazioni PVP' in detail_data:
                            auction_data['pvp_notes'] = detail_data['Annotazioni PVP']
                        
                        # Raw details per debugging
                        auction_data['raw_data'] = detail_data
                    
                    # Normalizza property_type (default se non disponibile)
                    auction_data['property_type'] = 'Immobile'
                    
                    auctions.append(auction_data)
                    
                except Exception as e:
                    logger.warning("fallcoaste_parse_item_failed", error=str(e))
                    continue
            
            logger.info("fallcoaste_parsed_page", count=len(auctions))
            return auctions
            
        except Exception as e:
            logger.error("fallcoaste_parse_page_failed", error=str(e))
            return []
    
    async def run(self, max_pages: int = 10, enrichment_mode: bool = True):
        """
        Main scraping loop for Fallcoaste.
        
        Args:
            max_pages: Maximum pages to scrape
            enrichment_mode: If True (DEFAULT), use fuzzy matching to enrich existing PVP auctions
                           If False, create new auction records (not recommended)
        """
        logger.info(
            "fallcoaste_starting_scraper",
            max_pages=max_pages,
            mode="enrichment" if enrichment_mode else "standalone"
        )
        
        # Fetch all PVP auctions once for matching
        pvp_auctions = []
        if enrichment_mode:
            pvp_auctions = await fetch_pvp_auctions_from_backend()
            if not pvp_auctions:
                logger.warning("no_pvp_auctions_found", message="Cannot enrich without PVP data, skipping")
                return
        
        total_auctions = 0
        total_enrichments = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        for page in range(1, max_pages + 1):
            try:
                # Fetch HTML page
                html = await self.fetch_page(page)
                
                if html is None:
                    consecutive_failures += 1
                    logger.warning(
                        "fallcoaste_no_html",
                        page=page,
                        consecutive_failures=consecutive_failures
                    )
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(
                            "fallcoaste_too_many_failures",
                            reason="stopping_to_avoid_server_overload"
                        )
                        break
                    
                    # Wait longer after failures
                    await asyncio.sleep(settings.SCRAPER_DELAY_MS / 1000.0 * (consecutive_failures + 1))
                    continue
                
                # Parse auctions
                auctions = await self.parse_auction_list(html)
                
                if not auctions:
                    consecutive_failures += 1
                    logger.warning("fallcoaste_empty_page", page=page, consecutive_failures=consecutive_failures)
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(
                            "fallcoaste_too_many_empty_pages",
                            reason="stopping_to_avoid_server_overload"
                        )
                        break
                    
                    await asyncio.sleep(settings.SCRAPER_DELAY_MS / 1000.0 * 3)
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # Process each auction based on mode
                for auction in auctions:
                    try:
                        total_auctions += 1
                        
                        if enrichment_mode:
                            # ENRICHMENT MODE: Find and enrich matching PVP auction
                            match_result = find_best_match(auction, pvp_auctions, min_score=0.7)
                            
                            if match_result:
                                pvp_auction, confidence = match_result
                                
                                # Enrich the PVP auction
                                enriched = enrich_pvp_auction(pvp_auction, auction, confidence)
                                
                                # Publish enriched auction (will update existing record)
                                await publish_auction_data(enriched)
                                total_enrichments += 1
                                
                                logger.info(
                                    "fallcoaste_enriched_auction",
                                    pvp_id=pvp_auction.get('external_id'),
                                    fallcoaste_city=auction.get('city'),
                                    confidence=f"{confidence:.2f}",
                                    added_photos=bool(auction.get('photos')),
                                    added_coords=bool(auction.get('latitude'))
                                )
                            else:
                                logger.debug(
                                    "fallcoaste_no_match_found",
                                    fallcoaste_city=auction.get('city'),
                                    fallcoaste_court=auction.get('court'),
                                    fallcoaste_price=auction.get('base_price')
                                )
                        else:
                            # STANDALONE MODE: Create new auction record (not recommended)
                            await publish_auction_data(auction)
                            logger.debug("fallcoaste_created_new_auction", auction_id=auction.get('external_id'))
                    
                    except Exception as e:
                        logger.error(
                            "fallcoaste_process_failed",
                            auction_id=auction.get('external_id'),
                            error=str(e)
                        )
                
                # Polite delay between pages
                base_delay = settings.SCRAPER_DELAY_MS / 1000.0
                jitter = random.uniform(0, base_delay * 0.5)
                await asyncio.sleep(base_delay + jitter)
            
            except Exception as e:
                consecutive_failures += 1
                logger.error(
                    "fallcoaste_scraping_error",
                    page=page,
                    error=str(e),
                    consecutive_failures=consecutive_failures
                )
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(
                        "fallcoaste_too_many_errors",
                        reason="stopping_to_avoid_server_overload"
                    )
                    break
                
                # Exponential backoff after errors
                wait_time = settings.SCRAPER_DELAY_MS / 1000.0 * (2 ** consecutive_failures)
                logger.info("fallcoaste_backing_off", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
                continue
        
        if enrichment_mode:
            enrichment_rate = (total_enrichments / total_auctions * 100) if total_auctions > 0 else 0
            logger.info(
                "fallcoaste_enrichment_completed",
                total_processed=total_auctions,
                total_enriched=total_enrichments,
                enrichment_rate=f"{enrichment_rate:.1f}%",
                final_consecutive_failures=consecutive_failures
            )
        else:
            logger.info(
                "fallcoaste_scraping_completed",
                total_auctions=total_auctions,
                final_consecutive_failures=consecutive_failures
            )


async def main():
    """Entry point for Fallcoaste scraper."""
    async with FallcoasteScraper() as scraper:
        await scraper.run(max_pages=50)  # 50 pagine per coprire buona parte del catalogo


if __name__ == "__main__":
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    asyncio.run(main())
