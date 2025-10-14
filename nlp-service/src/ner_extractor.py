"""
Named Entity Recognition (NER) for Italian real estate text.
Extracts: property type, city, price, surface, court, dates.
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Try to import spaCy, fallback to regex-only if not available
try:
    import spacy
    nlp = spacy.load("it_core_news_lg")
    SPACY_AVAILABLE = True
except:
    SPACY_AVAILABLE = False
    logger.warning("spacy_not_available", message="Using regex-only extraction")


PROPERTY_TYPES = {
    'appartamento': 'Appartamento',
    'alloggio': 'Appartamento',
    'casa': 'Appartamento',
    'bilocale': 'Appartamento',
    'trilocale': 'Appartamento',
    'villa': 'Villa',
    'villetta': 'Villa',
    'attico': 'Attico',
    'superattico': 'Attico',
    'penthouse': 'Attico',
    'negozio': 'Locale Commerciale',
    'locale commerciale': 'Locale Commerciale',
    'ufficio': 'Ufficio',
    'studio': 'Ufficio',
    'magazzino': 'Magazzino',
    'deposito': 'Magazzino',
    'capannone': 'Magazzino',
    'box': 'Box',
    'garage': 'Box',
    'autorimessa': 'Box',
    'terreno': 'Terreno',
    'lotto': 'Terreno',
    'rustico': 'Rustico',
    'casale': 'Rustico',
}

ITALIAN_CITIES = [
    'Roma', 'Milano', 'Napoli', 'Torino', 'Palermo', 'Genova', 'Bologna',
    'Firenze', 'Bari', 'Catania', 'Venezia', 'Verona', 'Messina', 'Padova',
    'Trieste', 'Brescia', 'Parma', 'Taranto', 'Prato', 'Modena', 'Reggio Calabria',
]


def extract_property_type(text: str) -> Optional[str]:
    """Extract property type from text."""
    text_lower = text.lower()
    
    for keyword, prop_type in PROPERTY_TYPES.items():
        if keyword in text_lower:
            return prop_type
    
    return "Altro"


def extract_city(text: str) -> Optional[str]:
    """Extract city name from text."""
    if SPACY_AVAILABLE:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "LOC" or ent.label_ == "GPE":
                # Check if it's a known Italian city
                if ent.text in ITALIAN_CITIES:
                    return ent.text
    
    # Fallback: check for known cities in text
    for city in ITALIAN_CITIES:
        if city.lower() in text.lower():
            return city
    
    return None


def extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    patterns = [
        r'(?:prezzo base|base d\'?asta|valore).*?€?\s*([\d.,]+)',
        r'€\s*([\d.,]+)',
        r'([\d]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*€',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                price_str = match.group(1)
                price_str = price_str.replace('.', '').replace(',', '.')
                price = float(price_str)
                
                # Sanity check
                if 1000 <= price <= 100000000:
                    return price
            except ValueError:
                continue
    
    return None


def extract_surface(text: str) -> Optional[float]:
    """Extract surface area in square meters."""
    patterns = [
        r'(\d+)\s*(?:mq|m2|m²|metri quadri)',
        r'superficie.*?(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                surface = float(match.group(1))
                if 10 <= surface <= 10000:
                    return surface
            except ValueError:
                continue
    
    return None


def extract_rooms(text: str) -> Optional[int]:
    """Extract number of rooms."""
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
    
    match = re.search(r'(\d+)\s*(?:vani|locali|camere)', text, re.IGNORECASE)
    if match:
        try:
            rooms = int(match.group(1))
            if 1 <= rooms <= 20:
                return rooms
        except ValueError:
            pass
    
    return None


def extract_court(text: str) -> Optional[str]:
    """Extract court/tribunal name."""
    patterns = [
        r'Tribunale\s+(?:di\s+)?([A-Z][a-zà-ù]+)',
        r'Tribunale\s+([A-Z][a-zà-ù]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"Tribunale di {match.group(1)}"
    
    return None


def extract_auction_date(text: str) -> Optional[str]:
    """Extract auction date."""
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    if match.group(2).isdigit():
                        # DD/MM/YYYY format
                        day, month, year = match.groups()
                        date_obj = datetime(int(year), int(month), int(day))
                    else:
                        # DD Month YYYY format
                        months = {
                            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
                            'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
                            'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
                        }
                        day = int(match.group(1))
                        month = months.get(match.group(2).lower(), 1)
                        year = int(match.group(3))
                        date_obj = datetime(year, month, day)
                    
                    return date_obj.isoformat()
            except ValueError:
                continue
    
    return None


def extract_entities(title: str, description: str, full_text: str) -> Dict[str, Any]:
    """
    Extract all entities from auction text.
    
    Args:
        title: Auction title
        description: Auction description
        full_text: Full auction text
    
    Returns:
        Dictionary of extracted entities
    """
    combined_text = f"{title} {description} {full_text}"
    
    entities = {}
    
    # Extract property type
    prop_type = extract_property_type(combined_text)
    if prop_type:
        entities['property_type'] = prop_type
    
    # Extract city
    city = extract_city(combined_text)
    if city:
        entities['city'] = city
    
    # Extract price
    price = extract_price(combined_text)
    if price:
        entities['base_price'] = price
    
    # Extract surface
    surface = extract_surface(combined_text)
    if surface:
        entities['surface_sqm'] = surface
    
    # Extract rooms
    rooms = extract_rooms(combined_text)
    if rooms:
        entities['rooms'] = rooms
    
    # Extract court
    court = extract_court(combined_text)
    if court:
        entities['court'] = court
    
    # Extract auction date
    auction_date = extract_auction_date(combined_text)
    if auction_date:
        entities['auction_date'] = auction_date
    
    logger.debug(
        "entities_extracted",
        entities_count=len(entities),
        has_price=bool(price),
        has_city=bool(city)
    )
    
    return entities
