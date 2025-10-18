"""
Fuzzy matching utilities for enriching PVP auctions with Fallcoaste data.

Matches on: address, tribunal, auction_date, base_price
Enriches with: photos, floor_plans, coordinates, documents
"""
import structlog
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher
from datetime import datetime
import re
import aiohttp

logger = structlog.get_logger()


def normalize_string(s: str) -> str:
    """Normalize string for comparison (lowercase, strip, normalize spaces)."""
    if not s:
        return ""
    # Convert to lowercase
    s = s.lower()
    # Remove extra spaces
    s = re.sub(r'\s+', ' ', s)
    # Remove punctuation for comparison
    s = re.sub(r'[^\w\s]', '', s)
    return s.strip()


def fuzzy_match_score(str1: str, str2: str) -> float:
    """
    Calculate fuzzy match score between two strings (0.0 to 1.0).
    Uses SequenceMatcher for similarity.
    """
    if not str1 or not str2:
        return 0.0
    
    norm1 = normalize_string(str1)
    norm2 = normalize_string(str2)
    
    if not norm1 or not norm2:
        return 0.0
    
    return SequenceMatcher(None, norm1, norm2).ratio()


def parse_price(price_text: str) -> Optional[float]:
    """Extract numeric price from text."""
    if not price_text:
        return None
    
    # Remove currency symbols and spaces
    price_text = re.sub(r'[€$\s]', '', str(price_text))
    # Remove thousands separators
    price_text = price_text.replace('.', '').replace(',', '.')
    
    try:
        return float(price_text)
    except (ValueError, TypeError):
        return None


def parse_date(date_text: str) -> Optional[datetime]:
    """Parse Italian date format."""
    if not date_text:
        return None
    
    # Try common Italian formats
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_text.strip(), fmt)
        except ValueError:
            continue
    
    return None


def match_auction(pvp_auction: Dict[str, Any], fallcoaste_auction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate match score between PVP and Fallcoaste auctions.
    
    Returns:
        {
            'is_match': bool,
            'confidence': float (0.0 to 1.0),
            'scores': {
                'address': float,
                'tribunal': float,
                'price': float,
                'date': float
            }
        }
    """
    scores = {}
    weights = {
        'address': 0.35,    # Indirizzo - peso maggiore
        'tribunal': 0.30,   # Tribunale - peso alto
        'price': 0.20,      # Prezzo base - medio
        'date': 0.15        # Data asta - peso minore (può variare)
    }
    
    # 1. Address matching
    pvp_address = f"{pvp_auction.get('address', '')} {pvp_auction.get('city', '')}"
    fall_address = fallcoaste_auction.get('address', '')
    scores['address'] = fuzzy_match_score(pvp_address, fall_address)
    
    # 2. Tribunal matching
    pvp_court = pvp_auction.get('court', '')
    fall_court = fallcoaste_auction.get('Tribunale', '')
    scores['tribunal'] = fuzzy_match_score(pvp_court, fall_court)
    
    # 3. Price matching (tolerance of 5%)
    pvp_price = pvp_auction.get('base_price')
    fall_price_text = fallcoaste_auction.get('Prezzo base', '')
    fall_price = parse_price(fall_price_text)
    
    if pvp_price and fall_price:
        price_diff = abs(pvp_price - fall_price) / max(pvp_price, fall_price)
        # Convert to similarity score (1.0 = same, 0.0 = very different)
        scores['price'] = max(0.0, 1.0 - price_diff)
    else:
        scores['price'] = 0.0
    
    # 4. Date matching (same day = good match)
    pvp_date_str = pvp_auction.get('auction_date', '')
    fall_date_str = fallcoaste_auction.get('Data vendita', '')
    
    pvp_date = parse_date(pvp_date_str)
    fall_date = parse_date(fall_date_str)
    
    if pvp_date and fall_date:
        # Same day = 1.0, different day = decrease score
        days_diff = abs((pvp_date - fall_date).days)
        if days_diff == 0:
            scores['date'] = 1.0
        elif days_diff <= 7:
            scores['date'] = 0.7
        elif days_diff <= 30:
            scores['date'] = 0.4
        else:
            scores['date'] = 0.0
    else:
        scores['date'] = 0.0
    
    # Calculate weighted confidence
    confidence = sum(scores[key] * weights[key] for key in weights.keys())
    
    # Match threshold: 0.70 (70% confidence)
    is_match = confidence >= 0.70
    
    logger.debug(
        "match_calculated",
        pvp_id=pvp_auction.get('external_id'),
        fall_id=fallcoaste_auction.get('external_id'),
        confidence=confidence,
        is_match=is_match,
        scores=scores
    )
    
    return {
        'is_match': is_match,
        'confidence': confidence,
        'scores': scores
    }


async def enrich_pvp_auction(
    pvp_auction: Dict[str, Any],
    fallcoaste_auction: Dict[str, Any],
    session: aiohttp.ClientSession
) -> Dict[str, Any]:
    """
    Enrich PVP auction with Fallcoaste data.
    
    Adds:
    - Photos (images)
    - Floor plans (planimetrie)
    - Additional coordinates if better
    - Documents
    - Additional details
    """
    enriched = pvp_auction.copy()
    
    # Coordinate enrichment (if PVP doesn't have them)
    if not pvp_auction.get('latitude') and fallcoaste_auction.get('latitude'):
        enriched['latitude'] = fallcoaste_auction['latitude']
        enriched['longitude'] = fallcoaste_auction['longitude']
        logger.info("enriched_coordinates", pvp_id=pvp_auction['external_id'])
    
    # Photos enrichment
    if fallcoaste_auction.get('photos'):
        enriched['photos'] = fallcoaste_auction['photos']
        logger.info("enriched_photos", pvp_id=pvp_auction['external_id'], count=len(fallcoaste_auction['photos']))
    
    # Floor plans enrichment
    if fallcoaste_auction.get('floor_plans'):
        enriched['floor_plans'] = fallcoaste_auction['floor_plans']
        logger.info("enriched_floor_plans", pvp_id=pvp_auction['external_id'])
    
    # Documents enrichment
    if fallcoaste_auction.get('documents'):
        enriched['documents'] = fallcoaste_auction['documents']
        logger.info("enriched_documents", pvp_id=pvp_auction['external_id'])
    
    # Additional details
    enrichment_details = {
        'fallcoaste_url': fallcoaste_auction.get('url'),
        'fallcoaste_id': fallcoaste_auction.get('external_id'),
        'enriched_at': datetime.utcnow().isoformat()
    }
    
    enriched['enrichment'] = enrichment_details
    
    return enriched


async def find_matching_pvp_auctions(
    fallcoaste_auction: Dict[str, Any],
    session: aiohttp.ClientSession,
    backend_url: str = "http://backend:8000"
) -> List[Dict[str, Any]]:
    """
    Find PVP auctions that could match the Fallcoaste auction.
    
    Uses backend API to search for candidates based on:
    - City
    - Province  
    - Court
    """
    try:
        # Extract search criteria from Fallcoaste auction
        city = fallcoaste_auction.get('city', '')
        province = fallcoaste_auction.get('province', '')
        
        # Search for candidate auctions
        params = {}
        if city:
            params['city'] = city
        if province:
            params['province'] = province
        
        # Limit to recent auctions (more likely to match)
        params['limit'] = 50
        
        async with session.get(f"{backend_url}/api/v1/auctions", params=params) as response:
            if response.status == 200:
                data = await response.json()
                candidates = data.get('items', [])
                logger.debug(
                    "pvp_candidates_found",
                    fall_id=fallcoaste_auction.get('external_id'),
                    count=len(candidates)
                )
                return candidates
            else:
                logger.error("backend_search_failed", status=response.status)
                return []
    
    except Exception as e:
        logger.error("find_candidates_failed", error=str(e))
        return []
