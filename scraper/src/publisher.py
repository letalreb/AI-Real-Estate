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
