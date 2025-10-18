"""
Fuzzy matching utilities for auction data enrichment.
Matches Fallcoaste data with PVP auctions based on multiple criteria.
"""
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


def normalize_string(s: str) -> str:
    """Normalize string for comparison (lowercase, strip, remove extra spaces)."""
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def similarity_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    s1_norm = normalize_string(s1)
    s2_norm = normalize_string(s2)
    
    if not s1_norm or not s2_norm:
        return 0.0
    
    return SequenceMatcher(None, s1_norm, s2_norm).ratio()


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date from various formats."""
    if not date_str:
        return None
    
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    
    return None


def dates_match(date1_str: str, date2_str: str, tolerance_days: int = 7) -> bool:
    """Check if two dates match within tolerance."""
    date1 = parse_date(date1_str)
    date2 = parse_date(date2_str)
    
    if not date1 or not date2:
        return False
    
    diff = abs((date1 - date2).days)
    return diff <= tolerance_days


def prices_match(price1: Optional[float], price2: Optional[float], tolerance_percent: float = 5.0) -> bool:
    """Check if two prices match within tolerance percentage."""
    if price1 is None or price2 is None:
        return False
    
    if price1 == 0 or price2 == 0:
        return False
    
    diff_percent = abs(price1 - price2) / max(price1, price2) * 100
    return diff_percent <= tolerance_percent


def calculate_match_score(pvp_auction: Dict[str, Any], fallcoaste_auction: Dict[str, Any]) -> float:
    """
    Calculate fuzzy match score between PVP and Fallcoaste auctions.
    Returns score from 0.0 (no match) to 1.0 (perfect match).
    
    Matching criteria:
    - Indirizzo (address): 30% weight
    - Tribunale (court): 25% weight
    - Data asta (auction date): 25% weight
    - Prezzo base (base price): 20% weight
    """
    score = 0.0
    
    # 1. Address similarity (30%)
    pvp_address = f"{pvp_auction.get('address', '')} {pvp_auction.get('city', '')}"
    fallcoaste_address = fallcoaste_auction.get('address', '')
    
    address_similarity = similarity_ratio(pvp_address, fallcoaste_address)
    score += address_similarity * 0.30
    
    # 2. Court similarity (25%)
    pvp_court = pvp_auction.get('court', '')
    fallcoaste_court = fallcoaste_auction.get('court', '')
    
    court_similarity = similarity_ratio(pvp_court, fallcoaste_court)
    score += court_similarity * 0.25
    
    # 3. Auction date match (25%)
    pvp_date = pvp_auction.get('auction_date', '')
    fallcoaste_date = fallcoaste_auction.get('auction_date', '')
    
    if dates_match(pvp_date, fallcoaste_date, tolerance_days=7):
        score += 0.25
    
    # 4. Price match (20%)
    pvp_price = pvp_auction.get('base_price')
    fallcoaste_price = fallcoaste_auction.get('base_price')
    
    if prices_match(pvp_price, fallcoaste_price, tolerance_percent=5.0):
        score += 0.20
    
    return score


def find_best_match(
    fallcoaste_auction: Dict[str, Any],
    pvp_auctions: List[Dict[str, Any]],
    min_score: float = 0.7
) -> Optional[tuple[Dict[str, Any], float]]:
    """
    Find best matching PVP auction for a Fallcoaste auction.
    Returns (pvp_auction, score) if match found above threshold, else None.
    """
    best_match = None
    best_score = 0.0
    
    for pvp_auction in pvp_auctions:
        score = calculate_match_score(pvp_auction, fallcoaste_auction)
        
        if score > best_score and score >= min_score:
            best_score = score
            best_match = pvp_auction
    
    if best_match:
        logger.debug(
            "found_match",
            pvp_id=best_match.get('external_id'),
            fallcoaste_city=fallcoaste_auction.get('city'),
            score=best_score
        )
        return (best_match, best_score)
    
    return None


def enrich_pvp_auction(
    pvp_auction: Dict[str, Any],
    fallcoaste_auction: Dict[str, Any],
    match_score: float
) -> Dict[str, Any]:
    """
    Enrich PVP auction with data from Fallcoaste.
    Only adds missing data, doesn't overwrite PVP (source of truth).
    """
    enriched = pvp_auction.copy()
    
    # Add enrichment metadata
    enriched['enriched_from_fallcoaste'] = True
    enriched['enrichment_score'] = match_score
    enriched['fallcoaste_url'] = fallcoaste_auction.get('url')
    
    # Enrich with photos (only if missing in PVP)
    if not enriched.get('photos') and fallcoaste_auction.get('photos'):
        enriched['photos'] = fallcoaste_auction['photos']
        logger.debug("enriched_photos", pvp_id=enriched.get('external_id'))
    
    # Enrich with floor plans (only if missing in PVP)
    if not enriched.get('floor_plans') and fallcoaste_auction.get('floor_plans'):
        enriched['floor_plans'] = fallcoaste_auction['floor_plans']
        logger.debug("enriched_floor_plans", pvp_id=enriched.get('external_id'))
    
    # Enrich with coordinates (only if missing in PVP)
    if (not enriched.get('latitude') or not enriched.get('longitude')):
        if fallcoaste_auction.get('latitude') and fallcoaste_auction.get('longitude'):
            enriched['latitude'] = fallcoaste_auction['latitude']
            enriched['longitude'] = fallcoaste_auction['longitude']
            logger.debug("enriched_coordinates", pvp_id=enriched.get('external_id'))
    
    # Enrich with documents (only if missing in PVP)
    if not enriched.get('documents') and fallcoaste_auction.get('documents'):
        enriched['documents'] = fallcoaste_auction['documents']
        logger.debug("enriched_documents", pvp_id=enriched.get('external_id'))
    
    # Add additional details as metadata
    enriched['fallcoaste_details'] = {
        'procedura_n': fallcoaste_auction.get('procedura_n'),
        'tipo_procedura': fallcoaste_auction.get('tipo_procedura'),
        'referente_procedura': fallcoaste_auction.get('referente_procedura'),
        'termine_presentazione': fallcoaste_auction.get('termine_presentazione'),
        'termine_visita': fallcoaste_auction.get('termine_visita'),
        'cauzione_minima': fallcoaste_auction.get('cauzione_minima'),
        'annotazioni': fallcoaste_auction.get('annotazioni'),
    }
    
    return enriched
