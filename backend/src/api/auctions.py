"""
Auction API endpoints.
CRUD operations and search functionality for auctions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from geoalchemy2.functions import ST_Distance, ST_GeogFromText, ST_AsText
import structlog

from ..database import get_db
from ..models import Auction, PropertyType, AuctionStatus
from ..schemas import (
    AuctionResponse,
    AuctionListResponse,
    AuctionFilters,
    SearchQuery,
    SearchResponse,
    SearchResult,
    MarketStats
)
from ..auth import get_current_user, User

logger = structlog.get_logger()

router = APIRouter()


@router.get("/auctions", response_model=AuctionListResponse)
async def list_auctions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_score: Optional[float] = None,
    status: AuctionStatus = AuctionStatus.ACTIVE,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of auctions with filters.
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - city: Filter by city name
    - property_type: Filter by property type
    - min_price: Minimum base price
    - max_price: Maximum base price
    - min_score: Minimum AI score (0-100)
    - status: Auction status (default: active)
    """
    # Build query
    query = select(Auction)
    
    # Apply filters
    filters = []
    if status:
        filters.append(Auction.status == status)
    if city:
        filters.append(Auction.city.ilike(f"%{city}%"))
    if property_type:
        filters.append(Auction.property_type == property_type)
    if min_price:
        filters.append(Auction.base_price >= min_price)
    if max_price:
        filters.append(Auction.base_price <= max_price)
    if min_score:
        filters.append(Auction.ai_score >= min_score)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total
    count_query = select(func.count()).select_from(Auction)
    if filters:
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Auction.ai_score.desc().nullslast())
    
    # Execute query
    result = await db.execute(query)
    auctions = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size
    
    logger.info(
        "list_auctions",
        total=total,
        page=page,
        filters={
            "city": city,
            "property_type": property_type,
            "min_score": min_score
        }
    )
    
    return AuctionListResponse(
        items=auctions,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/auctions/{auction_id}", response_model=AuctionResponse)
async def get_auction(
    auction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific auction.
    
    Path Parameters:
    - auction_id: Auction ID
    """
    query = select(Auction).where(Auction.id == auction_id)
    result = await db.execute(query)
    auction = result.scalar_one_or_none()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Auction with id {auction_id} not found"
        )
    
    logger.info("get_auction", auction_id=auction_id)
    
    return auction


@router.get("/auctions/search/text", response_model=AuctionListResponse)
async def search_auctions_text(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search auctions by text query (title, description, address).
    
    Query Parameters:
    - q: Search query
    - page: Page number
    - page_size: Items per page
    """
    # Simple text search across multiple fields
    search_filter = or_(
        Auction.title.ilike(f"%{q}%"),
        Auction.description.ilike(f"%{q}%"),
        Auction.address.ilike(f"%{q}%"),
        Auction.city.ilike(f"%{q}%")
    )
    
    query = select(Auction).where(
        and_(
            Auction.status == AuctionStatus.ACTIVE,
            search_filter
        )
    )
    
    # Count total
    count_query = select(func.count()).select_from(Auction).where(
        and_(
            Auction.status == AuctionStatus.ACTIVE,
            search_filter
        )
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Auction.ai_score.desc().nullslast())
    
    result = await db.execute(query)
    auctions = result.scalars().all()
    
    pages = (total + page_size - 1) // page_size
    
    logger.info("search_auctions_text", query=q, total=total)
    
    return AuctionListResponse(
        items=auctions,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/auctions/nearby/{auction_id}", response_model=List[AuctionResponse])
async def get_nearby_auctions(
    auction_id: int,
    radius_km: float = Query(10.0, ge=0.1, le=100),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get auctions near a specific auction (by geographic proximity).
    
    Path Parameters:
    - auction_id: Reference auction ID
    
    Query Parameters:
    - radius_km: Search radius in kilometers (default: 10km)
    - limit: Maximum number of results (default: 10)
    """
    # Get reference auction
    ref_query = select(Auction).where(Auction.id == auction_id)
    ref_result = await db.execute(ref_query)
    ref_auction = ref_result.scalar_one_or_none()
    
    if not ref_auction or not ref_auction.coordinates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found or has no coordinates"
        )
    
    # Query nearby auctions using PostGIS
    # ST_Distance returns distance in meters
    distance_expr = ST_Distance(
        Auction.coordinates,
        ref_auction.coordinates
    )
    
    query = select(Auction).where(
        and_(
            Auction.id != auction_id,
            Auction.status == AuctionStatus.ACTIVE,
            Auction.coordinates.isnot(None),
            distance_expr <= radius_km * 1000
        )
    ).order_by(distance_expr).limit(limit)
    
    result = await db.execute(query)
    nearby = result.scalars().all()
    
    logger.info(
        "get_nearby_auctions",
        auction_id=auction_id,
        radius_km=radius_km,
        found=len(nearby)
    )
    
    return nearby


@router.get("/stats/market", response_model=MarketStats)
async def get_market_stats(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get market statistics and aggregations.
    
    Query Parameters:
    - city: Filter by city (optional)
    """
    filters = [Auction.status == AuctionStatus.ACTIVE]
    if city:
        filters.append(Auction.city.ilike(f"%{city}%"))
    
    # Total and active auctions
    total_query = select(func.count()).select_from(Auction).where(and_(*filters))
    total_result = await db.execute(total_query)
    total_auctions = total_result.scalar()
    
    # Average price and score
    avg_query = select(
        func.avg(Auction.base_price),
        func.avg(Auction.ai_score)
    ).where(and_(*filters))
    avg_result = await db.execute(avg_query)
    avg_price, avg_score = avg_result.one()
    
    # Property type distribution
    type_query = select(
        Auction.property_type,
        func.count()
    ).where(and_(*filters)).group_by(Auction.property_type)
    type_result = await db.execute(type_query)
    property_dist = {str(pt): count for pt, count in type_result.all()}
    
    # City distribution (top 10)
    city_query = select(
        Auction.city,
        func.count()
    ).where(and_(*filters)).group_by(Auction.city).order_by(func.count().desc()).limit(10)
    city_result = await db.execute(city_query)
    city_dist = {city: count for city, count in city_result.all() if city}
    
    # Price ranges
    price_ranges = {}
    for range_name, min_p, max_p in [
        ("0-50k", 0, 50000),
        ("50k-100k", 50000, 100000),
        ("100k-250k", 100000, 250000),
        ("250k-500k", 250000, 500000),
        ("500k+", 500000, float('inf'))
    ]:
        range_filters = filters + [
            Auction.base_price >= min_p,
            Auction.base_price < max_p if max_p != float('inf') else Auction.base_price >= min_p
        ]
        range_query = select(func.count()).select_from(Auction).where(and_(*range_filters))
        range_result = await db.execute(range_query)
        price_ranges[range_name] = range_result.scalar()
    
    return MarketStats(
        total_auctions=total_auctions,
        active_auctions=total_auctions,
        avg_base_price=float(avg_price) if avg_price else 0.0,
        avg_score=float(avg_score) if avg_score else 0.0,
        property_type_distribution=property_dist,
        city_distribution=city_dist,
        price_ranges=price_ranges
    )
