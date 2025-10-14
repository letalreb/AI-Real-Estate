"""
Text normalization utilities.
Cleans and standardizes auction text data.
"""
import re
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    if not text:
        return ""
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep Italian accents
    text = re.sub(r'[^\w\s€.,;:()\-àèéìòù]', '', text, flags=re.UNICODE)
    
    return text.strip()


def normalize_price(price_text: str) -> float:
    """Extract and normalize price from text."""
    if not price_text:
        return 0.0
    
    # Remove currency symbols and clean
    price_text = price_text.replace('€', '').replace('EUR', '')
    
    # Remove thousand separators
    price_text = price_text.replace('.', '').replace(',', '.')
    
    # Extract number
    match = re.search(r'(\d+(?:\.\d{1,2})?)', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    
    return 0.0


def normalize_surface(text: str) -> float:
    """Extract surface area in square meters."""
    if not text:
        return 0.0
    
    # Look for patterns like "80 mq", "80m2", "80 metri quadri"
    patterns = [
        r'(\d+)\s*(?:mq|m2|m²)',
        r'(\d+)\s*metri\s*quadr[ia]',
        r'superficie.*?(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return 0.0


def normalize_rooms(text: str) -> int:
    """Extract number of rooms."""
    if not text:
        return 0
    
    # Check for specific terms
    mappings = {
        'monolocale': 1,
        'bilocale': 2,
        'trilocale': 3,
        'quadrilocale': 4,
    }
    
    text_lower = text.lower()
    for term, count in mappings.items():
        if term in text_lower:
            return count
    
    # Look for number + rooms/vani
    match = re.search(r'(\d+)\s*(?:vani|locali|stanze|camere)', text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return 0


def normalize_auction_text(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all text fields in auction data.
    
    Args:
        data: Raw auction data dictionary
    
    Returns:
        Normalized data dictionary
    """
    normalized = data.copy()
    
    # Clean text fields
    if 'title' in normalized:
        normalized['title'] = clean_text(normalized['title'])
    
    if 'description' in normalized:
        normalized['description'] = clean_text(normalized['description'])
    
    if 'full_text' in normalized:
        normalized['full_text'] = clean_text(normalized['full_text'])
    
    # Extract and normalize numeric fields
    if 'price_text' in normalized:
        normalized['base_price'] = normalize_price(normalized['price_text'])
    
    # Try to extract from full text if not already present
    full_text = normalized.get('full_text', '')
    
    if 'surface_sqm' not in normalized or not normalized.get('surface_sqm'):
        normalized['surface_sqm'] = normalize_surface(full_text)
    
    if 'rooms' not in normalized or not normalized.get('rooms'):
        normalized['rooms'] = normalize_rooms(full_text)
    
    logger.debug("text_normalized", auction_id=normalized.get('external_id'))
    
    return normalized
