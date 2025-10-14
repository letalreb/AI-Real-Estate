"""
Sample data generator for testing and development.
Creates realistic Italian real estate auction data.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import random
from sqlalchemy import select

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import AsyncSessionLocal
from src.models import Auction, PropertyType, AuctionStatus, User
from src.auth import get_password_hash
from src.config import settings

# Sample Italian cities with coordinates
CITIES = [
    {"name": "Roma", "lat": 41.9028, "lon": 12.4964, "province": "RM"},
    {"name": "Milano", "lat": 45.4642, "lon": 9.1900, "province": "MI"},
    {"name": "Napoli", "lat": 40.8518, "lon": 14.2681, "province": "NA"},
    {"name": "Torino", "lat": 45.0703, "lon": 7.6869, "province": "TO"},
    {"name": "Firenze", "lat": 43.7696, "lon": 11.2558, "province": "FI"},
    {"name": "Bologna", "lat": 44.4949, "lon": 11.3426, "province": "BO"},
    {"name": "Genova", "lat": 44.4056, "lon": 8.9463, "province": "GE"},
    {"name": "Palermo", "lat": 38.1157, "lon": 13.3615, "province": "PA"},
    {"name": "Bari", "lat": 41.1171, "lon": 16.8719, "province": "BA"},
    {"name": "Venezia", "lat": 45.4408, "lon": 12.3155, "province": "VE"},
]

PROPERTY_TYPES = [
    PropertyType.APPARTAMENTO,
    PropertyType.VILLA,
    PropertyType.ATTICO,
    PropertyType.LOCALE_COMMERCIALE,
    PropertyType.UFFICIO,
    PropertyType.BOX,
]

DESCRIPTIONS = [
    "Immobile di pregio situato in zona centrale",
    "Appartamento da ristrutturare con ampia metratura",
    "Villa indipendente con giardino e posto auto",
    "Locale commerciale su strada principale",
    "Ufficio in palazzo d'epoca recentemente ristrutturato",
    "Box auto doppio con accesso indipendente",
    "Attico con terrazzo panoramico e vista città",
]

COURTS = [
    "Tribunale di Roma",
    "Tribunale di Milano",
    "Tribunale di Napoli",
    "Tribunale di Torino",
    "Tribunale di Firenze",
]


def generate_auction_data(index: int) -> dict:
    """Generate realistic auction data."""
    city_data = random.choice(CITIES)
    property_type = random.choice(PROPERTY_TYPES)
    
    # Randomize coordinates slightly
    lat = city_data["lat"] + random.uniform(-0.1, 0.1)
    lon = city_data["lon"] + random.uniform(-0.1, 0.1)
    
    # Generate property details based on type
    if property_type == PropertyType.APPARTAMENTO:
        surface = random.randint(50, 150)
        rooms = random.randint(2, 5)
        bathrooms = random.randint(1, 3)
    elif property_type == PropertyType.VILLA:
        surface = random.randint(150, 400)
        rooms = random.randint(4, 10)
        bathrooms = random.randint(2, 5)
    elif property_type == PropertyType.BOX:
        surface = random.randint(15, 40)
        rooms = 1
        bathrooms = 0
    else:
        surface = random.randint(30, 200)
        rooms = random.randint(1, 6)
        bathrooms = random.randint(1, 3)
    
    # Base price calculation
    price_per_sqm = random.uniform(1000, 4000)
    base_price = surface * price_per_sqm
    
    # Add some randomness to pricing
    base_price *= random.uniform(0.6, 1.0)  # Auction discount
    
    # Estimated market value (higher than base price)
    estimated_value = base_price * random.uniform(1.2, 1.8)
    
    # Calculate AI score (simplified)
    discount = (estimated_value - base_price) / estimated_value
    ai_score = discount * 100 * random.uniform(0.8, 1.2)
    ai_score = max(10, min(100, ai_score))  # Clamp between 10-100
    
    # Random auction date in next 60 days
    auction_date = datetime.utcnow() + timedelta(days=random.randint(1, 60))
    
    return {
        "external_id": f"PVP-{city_data['province']}-{index:05d}",
        "title": f"{property_type.value} - {city_data['name']} - {surface}mq",
        "description": random.choice(DESCRIPTIONS),
        "property_type": property_type,
        "city": city_data["name"],
        "province": city_data["province"],
        "address": f"Via {random.choice(['Roma', 'Milano', 'Venezia', 'Garibaldi'])} {random.randint(1, 200)}",
        "latitude": lat,
        "longitude": lon,
        "surface_sqm": surface,
        "rooms": rooms,
        "bathrooms": bathrooms,
        "floor": random.randint(0, 8) if property_type == PropertyType.APPARTAMENTO else None,
        "base_price": round(base_price, 2),
        "current_price": round(base_price * random.uniform(0.9, 1.1), 2),
        "estimated_value": round(estimated_value, 2),
        "auction_date": auction_date,
        "auction_round": random.randint(1, 3),
        "court": random.choice(COURTS),
        "case_number": f"RGE {random.randint(100, 9999)}/{random.randint(2020, 2024)}",
        "status": AuctionStatus.ACTIVE,
        "is_occupied": random.random() < 0.2,  # 20% chance occupied
        "ai_score": round(ai_score, 2),
        "score_breakdown": {
            "price_discount": round(discount * 100, 2),
            "location_score": random.randint(50, 95),
            "property_condition": random.randint(40, 90),
            "legal_complexity": random.randint(30, 80),
            "liquidity_potential": random.randint(50, 95),
        },
        "source_url": f"https://pvp.giustizia.it/pvp/it/dettaglio.page?idAnnuncio={index}",
        "raw_data": {"sample": True},
    }


async def create_sample_data(num_auctions: int = 50):
    """Create sample auction data in database."""
    print(f"Creating {num_auctions} sample auctions...")
    
    async with AsyncSessionLocal() as session:
        # Create admin user if not exists
        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            print(f"Creating admin user: {settings.ADMIN_EMAIL}")
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_admin=True
            )
            session.add(admin_user)
        
        # Create sample auctions
        for i in range(1, num_auctions + 1):
            auction_data = generate_auction_data(i)
            
            # Check if auction already exists
            result = await session.execute(
                select(Auction).where(Auction.external_id == auction_data["external_id"])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Create point geometry from lat/lon
                from geoalchemy2 import WKTElement
                point = WKTElement(f"POINT({auction_data['longitude']} {auction_data['latitude']})", srid=4326)
                
                auction_data["coordinates"] = point
                auction = Auction(**auction_data)
                session.add(auction)
                
                if i % 10 == 0:
                    print(f"Created {i}/{num_auctions} auctions...")
        
        await session.commit()
        print("✅ Sample data created successfully!")
        
        # Print summary
        result = await session.execute(select(Auction))
        total = len(result.scalars().all())
        print(f"\nTotal auctions in database: {total}")


async def main():
    """Main entry point."""
    import sys
    
    num_auctions = 50
    if len(sys.argv) > 1:
        try:
            num_auctions = int(sys.argv[1])
        except ValueError:
            print("Usage: python sample_data.py [num_auctions]")
            sys.exit(1)
    
    await create_sample_data(num_auctions)


if __name__ == "__main__":
    asyncio.run(main())
