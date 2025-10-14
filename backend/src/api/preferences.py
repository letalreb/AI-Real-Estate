"""
Search preferences API endpoints.
Manage user saved searches and notification preferences.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import structlog

from ..database import get_db
from ..models import User, SearchPreference
from ..schemas import (
    SearchPreferenceCreate,
    SearchPreferenceUpdate,
    SearchPreferenceResponse
)
from ..auth import get_current_user

logger = structlog.get_logger()

router = APIRouter()


@router.get("/preferences", response_model=List[SearchPreferenceResponse])
async def list_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all search preferences for current user.
    
    Requires authentication.
    """
    query = select(SearchPreference).where(
        SearchPreference.user_id == current_user.id
    ).order_by(SearchPreference.created_at.desc())
    
    result = await db.execute(query)
    preferences = result.scalars().all()
    
    return preferences


@router.post("/preferences", response_model=SearchPreferenceResponse, status_code=status.HTTP_201_CREATED)
async def create_preference(
    preference_data: SearchPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new search preference.
    
    Request Body:
    - name: Preference name
    - filters: Search filters as JSON object
    - notify: Enable notifications for this search
    
    Requires authentication.
    """
    new_preference = SearchPreference(
        user_id=current_user.id,
        name=preference_data.name,
        filters=preference_data.filters,
        notify=preference_data.notify,
        is_active=True
    )
    
    db.add(new_preference)
    await db.commit()
    await db.refresh(new_preference)
    
    logger.info(
        "preference_created",
        user_id=current_user.id,
        preference_id=new_preference.id,
        name=new_preference.name
    )
    
    return new_preference


@router.get("/preferences/{preference_id}", response_model=SearchPreferenceResponse)
async def get_preference(
    preference_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific search preference.
    
    Path Parameters:
    - preference_id: Preference ID
    
    Requires authentication.
    """
    query = select(SearchPreference).where(
        SearchPreference.id == preference_id,
        SearchPreference.user_id == current_user.id
    )
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    return preference


@router.put("/preferences/{preference_id}", response_model=SearchPreferenceResponse)
async def update_preference(
    preference_id: int,
    preference_data: SearchPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a search preference.
    
    Path Parameters:
    - preference_id: Preference ID
    
    Request Body:
    - name: New name (optional)
    - filters: New filters (optional)
    - notify: Enable/disable notifications (optional)
    - is_active: Activate/deactivate preference (optional)
    
    Requires authentication.
    """
    query = select(SearchPreference).where(
        SearchPreference.id == preference_id,
        SearchPreference.user_id == current_user.id
    )
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    # Update fields
    if preference_data.name is not None:
        preference.name = preference_data.name
    if preference_data.filters is not None:
        preference.filters = preference_data.filters
    if preference_data.notify is not None:
        preference.notify = preference_data.notify
    if preference_data.is_active is not None:
        preference.is_active = preference_data.is_active
    
    await db.commit()
    await db.refresh(preference)
    
    logger.info(
        "preference_updated",
        user_id=current_user.id,
        preference_id=preference.id
    )
    
    return preference


@router.delete("/preferences/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(
    preference_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a search preference.
    
    Path Parameters:
    - preference_id: Preference ID
    
    Requires authentication.
    """
    query = select(SearchPreference).where(
        SearchPreference.id == preference_id,
        SearchPreference.user_id == current_user.id
    )
    result = await db.execute(query)
    preference = result.scalar_one_or_none()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preference not found"
        )
    
    await db.delete(preference)
    await db.commit()
    
    logger.info(
        "preference_deleted",
        user_id=current_user.id,
        preference_id=preference_id
    )
    
    return None
