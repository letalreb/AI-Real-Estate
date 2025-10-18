"""
Unified scraper orchestrator.

Strategy:
1. PVP Giustizia = Primary certified source
   - Download all auctions
   - Assign universal auction_id
   - This is the source of truth

2. Fallcoaste = Secondary enrichment source
   - Use fuzzy matching on: address, tribunal, auction_date, base_price
   - If match found, enrich PVP record with: photos, floor plans, coordinates, documents
   - Never create new auctions, only enrich existing ones
"""
import asyncio
import structlog
from .pvp_scraper import PVPScraper
from .fallcoaste_scraper import FallcoasteScraper

logger = structlog.get_logger()


async def run_unified_scraper():
    """
    Run all configured scrapers sequentially.
    
    Strategy:
    1. PVP = Source of truth, creates auction records with universal ID
    2. Fallcoaste = Enrichment source, uses fuzzy matching to add photos/coords/docs
    """
    logger.info("starting_unified_scraper")
    
    # 1. Scrape PVP Government Portal (Source of Truth)
    logger.info("starting_pvp_scraper", role="primary_source")
    try:
        async with PVPScraper() as pvp_scraper:
            await pvp_scraper.run(max_pages=100)
        logger.info("pvp_scraper_completed")
    except Exception as e:
        logger.error("pvp_scraper_failed", error=str(e))
    
    # Delay between sources to be polite
    logger.info("waiting_between_sources", seconds=10)
    await asyncio.sleep(10)
    
    # 2. Scrape Fallcoaste Professional Portal (Enrichment)
    logger.info("starting_fallcoaste_scraper", role="enrichment_source")
    try:
        async with FallcoasteScraper() as fallcoaste_scraper:
            # ENRICHMENT MODE: Match with PVP and add photos/coordinates/documents
            await fallcoaste_scraper.run(max_pages=50, enrichment_mode=True)
        logger.info("fallcoaste_scraper_completed")
    except Exception as e:
        logger.error("fallcoaste_scraper_failed", error=str(e))
    
    logger.info("unified_scraper_completed")


async def main():
    """Main entry point with periodic execution."""
    while True:
        try:
            logger.info("scraper_cycle_starting")
            await run_unified_scraper()
            logger.info("scraper_cycle_completed")
            
            # Wait 6 hours before next cycle (21600 seconds)
            logger.info("waiting_for_next_cycle", hours=6)
            await asyncio.sleep(21600)
        except Exception as e:
            logger.error("scraper_cycle_failed", error=str(e))
            # Wait 30 minutes on error
            logger.info("waiting_after_error", minutes=30)
            await asyncio.sleep(1800)


if __name__ == "__main__":
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    logger.info("starting_unified_scraper_service")
    asyncio.run(main())


async def main():
    """Entry point for unified scraper."""
    await run_unified_scraper()


if __name__ == "__main__":
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    asyncio.run(main())
