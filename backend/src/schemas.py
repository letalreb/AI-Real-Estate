"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class PropertyTypeEnum(str, Enum):
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


class AuctionStatusEnum(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Auction Schemas
class AuctionBase(BaseModel):
    title: str
    description: Optional[str] = None
    property_type: PropertyTypeEnum
    city: Optional[str] = None
    province: Optional[str] = None
    address: Optional[str] = None
    surface_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    base_price: float
    current_price: Optional[float] = None
    estimated_value: Optional[float] = None
    auction_date: Optional[datetime] = None
    court: Optional[str] = None
    status: AuctionStatusEnum = AuctionStatusEnum.ACTIVE


class AuctionCreate(AuctionBase):
    external_id: str
    source_url: Optional[str] = None


class AuctionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[float] = None
    status: Optional[AuctionStatusEnum] = None
    ai_score: Optional[float] = None


class AuctionResponse(AuctionBase):
    id: int
    external_id: str
    ai_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    source_url: Optional[str] = None
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Geographic coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        from_attributes = True


class AuctionListResponse(BaseModel):
    items: List[AuctionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuctionFilters(BaseModel):
    """Filters for auction search."""
    city: Optional[str] = None
    cities: Optional[List[str]] = None
    property_type: Optional[PropertyTypeEnum] = None
    property_types: Optional[List[PropertyTypeEnum]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_surface: Optional[float] = None
    max_surface: Optional[float] = None
    min_score: Optional[float] = None
    status: Optional[AuctionStatusEnum] = AuctionStatusEnum.ACTIVE
    
    # Geographic filters
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: Optional[float] = None


# Search Preference Schemas
class SearchPreferenceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    filters: Dict[str, Any]
    notify: bool = True


class SearchPreferenceCreate(SearchPreferenceBase):
    pass


class SearchPreferenceUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    notify: Optional[bool] = None
    is_active: Optional[bool] = None


class SearchPreferenceResponse(SearchPreferenceBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Notification Schemas
class NotificationBase(BaseModel):
    type: str
    title: str
    message: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: int
    auction_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    auction_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Search Schemas
class SearchQuery(BaseModel):
    q: str = Field(..., min_length=1)
    top_k: int = Field(20, ge=1, le=100)
    filters: Optional[AuctionFilters] = None


class SearchResult(BaseModel):
    auction: AuctionResponse
    score: float  # Similarity score


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str


# Statistics Schemas
class MarketStats(BaseModel):
    total_auctions: int
    active_auctions: int
    avg_base_price: float
    avg_score: float
    property_type_distribution: Dict[str, int]
    city_distribution: Dict[str, int]
    price_ranges: Dict[str, int]


# Health Check Schema
class HealthCheck(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
