"""
AI Ranking Engine.
Calculates convenience score (0-100) for each auction based on multiple factors.
"""
import yaml
from typing import Dict, Any, Tuple
import structlog
from pathlib import Path

logger = structlog.get_logger()

# Load configuration
CONFIG_PATH = Path("/app/config/config.yaml")
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
else:
    # Default configuration
    config = {
        'ranking': {
            'weights': {
                'price_discount': 0.30,
                'location_score': 0.25,
                'property_condition': 0.15,
                'legal_complexity': 0.15,
                'liquidity_potential': 0.15,
            }
        }
    }

WEIGHTS = config['ranking']['weights']


def estimate_market_value(data: Dict[str, Any]) -> float:
    """
    Estimate market value based on property characteristics.
    
    Uses simplified model based on:
    - Surface area
    - City tier
    - Property type
    """
    surface = data.get('surface_sqm', 80)
    city = data.get('city', '')
    property_type = data.get('property_type', 'Appartamento')
    
    # City tier pricing (EUR per sqm)
    tier_1_cities = ['Roma', 'Milano', 'Firenze', 'Bologna', 'Venezia']
    tier_2_cities = ['Torino', 'Napoli', 'Genova', 'Palermo', 'Bari']
    
    if city in tier_1_cities:
        base_price_sqm = 3500
    elif city in tier_2_cities:
        base_price_sqm = 2200
    else:
        base_price_sqm = 1500
    
    # Property type multiplier
    type_multipliers = {
        'Appartamento': 1.0,
        'Villa': 1.3,
        'Attico': 1.2,
        'Locale Commerciale': 0.9,
        'Ufficio': 0.95,
        'Box': 0.6,
        'Terreno': 0.3,
        'Rustico': 0.7,
    }
    
    multiplier = type_multipliers.get(property_type, 1.0)
    
    estimated_value = surface * base_price_sqm * multiplier
    
    return estimated_value


def calculate_price_discount_score(data: Dict[str, Any]) -> float:
    """
    Calculate score based on discount from market value.
    Higher discount = higher score.
    """
    base_price = data.get('base_price', 0)
    
    if not base_price or base_price <= 0:
        return 50.0  # Neutral score if no price
    
    # Get or estimate market value
    estimated_value = data.get('estimated_value')
    if not estimated_value:
        estimated_value = estimate_market_value(data)
    
    if estimated_value <= 0:
        return 50.0
    
    # Calculate discount percentage
    discount = (estimated_value - base_price) / estimated_value
    
    # Convert to 0-100 score
    # 0% discount = 0 score, 50% discount = 100 score
    score = discount * 200
    
    # Clamp between 0 and 100
    score = max(0, min(100, score))
    
    return score


def calculate_location_score(data: Dict[str, Any]) -> float:
    """
    Calculate location desirability score.
    Based on city tier and general desirability.
    """
    city = data.get('city', '')
    
    # Simple tier-based scoring
    tier_1 = ['Roma', 'Milano', 'Firenze', 'Bologna', 'Venezia', 'Torino']
    tier_2 = ['Napoli', 'Genova', 'Palermo', 'Bari', 'Catania', 'Verona']
    tier_3 = ['Padova', 'Trieste', 'Brescia', 'Parma', 'Modena', 'Reggio Emilia']
    
    if city in tier_1:
        return 90.0
    elif city in tier_2:
        return 75.0
    elif city in tier_3:
        return 65.0
    else:
        return 50.0


def calculate_property_condition_score(data: Dict[str, Any]) -> float:
    """
    Estimate property condition from description keywords.
    """
    description = data.get('description', '').lower()
    full_text = data.get('full_text', '').lower()
    combined = f"{description} {full_text}"
    
    excellent_keywords = ['ottimo', 'ristrutturato', 'nuovo', 'recente', 'moderno']
    good_keywords = ['buono', 'abitabile', 'discreto']
    fair_keywords = ['da ristrutturare', 'necessita lavori', 'da ammodernare']
    poor_keywords = ['pessimo', 'da demolire', 'rudere', 'collabente']
    
    if any(kw in combined for kw in excellent_keywords):
        return 90.0
    elif any(kw in combined for kw in good_keywords):
        return 75.0
    elif any(kw in combined for kw in fair_keywords):
        return 50.0
    elif any(kw in combined for kw in poor_keywords):
        return 25.0
    else:
        return 60.0  # Default/unknown


def calculate_legal_complexity_score(data: Dict[str, Any]) -> float:
    """
    Score based on legal complications (occupancy, liens, etc.).
    Lower complexity = higher score.
    """
    description = data.get('description', '').lower()
    full_text = data.get('full_text', '').lower()
    combined = f"{description} {full_text}"
    
    score = 70.0  # Base score
    
    # Negative factors
    if 'occupato' in combined:
        score -= 30
    if 'pignoramento' in combined:
        score -= 20
    if 'ipoteca' in combined:
        score -= 15
    
    # Positive factors
    if 'libero' in combined:
        score += 20
    if 'prima asta' in combined:
        score += 10
    
    # Auction round (later rounds may be better deals but riskier)
    auction_round = data.get('auction_round', 1)
    if auction_round == 2:
        score -= 5
    elif auction_round >= 3:
        score -= 10
    
    return max(0, min(100, score))


def calculate_liquidity_score(data: Dict[str, Any]) -> float:
    """
    Estimate resale potential / liquidity.
    """
    property_type = data.get('property_type', 'Appartamento')
    surface = data.get('surface_sqm', 80)
    
    # Property type liquidity
    type_scores = {
        'Appartamento': 90,
        'Attico': 85,
        'Villa': 70,
        'Ufficio': 65,
        'Locale Commerciale': 60,
        'Box': 75,
        'Magazzino': 50,
        'Terreno': 40,
        'Rustico': 45,
    }
    
    base_score = type_scores.get(property_type, 60)
    
    # Size preference (optimal 60-120 sqm for apartments)
    if property_type == 'Appartamento':
        if 60 <= surface <= 120:
            size_bonus = 10
        elif 40 <= surface < 60 or 120 < surface <= 150:
            size_bonus = 5
        else:
            size_bonus = 0
        
        base_score += size_bonus
    
    return min(100, base_score)


def calculate_ai_score(data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    Calculate overall AI convenience score (0-100).
    
    Args:
        data: Normalized auction data
    
    Returns:
        Tuple of (overall_score, score_breakdown)
    """
    # Calculate individual component scores
    price_score = calculate_price_discount_score(data)
    location_score = calculate_location_score(data)
    condition_score = calculate_property_condition_score(data)
    legal_score = calculate_legal_complexity_score(data)
    liquidity_score = calculate_liquidity_score(data)
    
    # Weighted average
    overall_score = (
        price_score * WEIGHTS['price_discount'] +
        location_score * WEIGHTS['location_score'] +
        condition_score * WEIGHTS['property_condition'] +
        legal_score * WEIGHTS['legal_complexity'] +
        liquidity_score * WEIGHTS['liquidity_potential']
    )
    
    # Ensure score is between 0 and 100
    overall_score = max(0, min(100, overall_score))
    
    breakdown = {
        'price_discount': round(price_score, 2),
        'location_score': round(location_score, 2),
        'property_condition': round(condition_score, 2),
        'legal_complexity': round(legal_score, 2),
        'liquidity_potential': round(liquidity_score, 2),
    }
    
    logger.info(
        "score_calculated",
        auction_id=data.get('external_id'),
        overall_score=round(overall_score, 2),
        price_score=round(price_score, 2),
        location_score=round(location_score, 2)
    )
    
    return round(overall_score, 2), breakdown
