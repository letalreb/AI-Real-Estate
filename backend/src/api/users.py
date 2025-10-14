"""
User management API endpoints.
Registration, login, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import structlog

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, UserLogin, Token
from ..auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user
)
from ..config import settings

logger = structlog.get_logger()

router = APIRouter()


@router.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Request Body:
    - email: User email (unique)
    - password: Password (min 8 characters)
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info("user_registered", user_id=new_user.id, email=new_user.email)
    
    return new_user


@router.post("/users/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    Request Body:
    - email: User email
    - password: User password
    
    Returns:
    - access_token: JWT token
    - token_type: "bearer"
    """
    user = await authenticate_user(credentials.email, credentials.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    logger.info("user_logged_in", user_id=user.id, email=user.email)
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile information.
    
    Requires authentication.
    """
    return current_user


@router.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    email: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    
    Request Body:
    - email: New email (optional)
    
    Requires authentication.
    """
    if email and email != current_user.email:
        # Check if new email is already taken
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        current_user.email = email
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info("user_updated", user_id=current_user.id)
    
    return current_user
