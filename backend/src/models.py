"""
Database models using SQLAlchemy ORM with PostGIS support.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from datetime import datetime
from typing import Optional
import enum

Base = declarative_base()


class PropertyType(str, enum.Enum):
    """Property type enumeration."""
    APPARTAMENTO = "Appartamento"
    VILLA = "Villa"
    ATTICO = "Attico"
    LOCALE_COMMERCIALE = "Locale Commerciale"
    UFFICIO = "Ufficio"
    MAGAZZINO = "Magazzino"
    TERRENO = "Terreno"
    BOX = "Box"
    RUSTICO = "Rustico"
    ALTRO = "Altro"


class AuctionStatus(str, enum.Enum):
    """Auction status enumeration."""
    ACTIVE = "active"
    ENDED = "ended"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    preferences = relationship("SearchPreference", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Auction(Base):
    """Auction model with geospatial support."""
    __tablename__ = "auctions"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    property_type = Column(Enum(PropertyType), nullable=False)
    
    # Location
    city = Column(String(100), index=True)
    province = Column(String(100))
    address = Column(String(500))
    coordinates = Column(Geometry('POINT', srid=4326))  # PostGIS point
    
    # Property details
    surface_sqm = Column(Float)
    rooms = Column(Integer)
    bathrooms = Column(Integer)
    floor = Column(Integer)
    
    # Auction details
    base_price = Column(Float, nullable=False)
    current_price = Column(Float)
    estimated_value = Column(Float)
    auction_date = Column(DateTime, index=True)
    auction_round = Column(Integer, default=1)
    court = Column(String(200))
    case_number = Column(String(100))
    
    # Status
    status = Column(Enum(AuctionStatus), default=AuctionStatus.ACTIVE, index=True)
    is_occupied = Column(Boolean, default=False)
    
    # AI Ranking
    ai_score = Column(Float, index=True)  # 0-100
    score_breakdown = Column(JSON)  # Detailed score components
    
    # Metadata
    source_url = Column(String(500))
    raw_data = Column(JSON)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Vector embedding reference
    embedding_id = Column(String(100))  # Qdrant point ID
    
    @property
    def latitude(self) -> Optional[float]:
        """Extract latitude from PostGIS coordinates."""
        if self.coordinates:
            from geoalchemy2.shape import to_shape
            point = to_shape(self.coordinates)
            return point.y
        return None
    
    @property
    def longitude(self) -> Optional[float]:
        """Extract longitude from PostGIS coordinates."""
        if self.coordinates:
            from geoalchemy2.shape import to_shape
            point = to_shape(self.coordinates)
            return point.x
        return None


class SearchPreference(Base):
    """User search preferences for notifications."""
    __tablename__ = "search_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    filters = Column(JSON, nullable=False)  # Search filters as JSON
    notify = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    auction_id = Column(Integer, ForeignKey("auctions.id"))
    
    type = Column(String(50), nullable=False)  # new_auction, price_drop, ending_soon
    title = Column(String(200), nullable=False)
    message = Column(Text)
    data = Column(JSON)
    
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    auction = relationship("Auction")


class ScrapingLog(Base):
    """Log of scraping activities."""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    
    auctions_found = Column(Integer, default=0)
    auctions_new = Column(Integer, default=0)
    auctions_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
