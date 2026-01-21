"""
Authentication API Endpoints
=============================

User registration, login, and profile management.

Endpoints:
- POST /auth/register - Create a new user account
- POST /auth/login    - Login and get JWT token
- GET  /auth/me       - Get current user profile
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.database import User
from schemas import Token, UserRegister, UserResponse
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    decode_access_token,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from services.db_service import get_db_session

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with get_db_session() as session:
        yield session


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """
    Get the current authenticated user from JWT token.

    Returns None if no token or invalid token (for optional auth).
    """
    if not token:
        return None

    token_data = decode_access_token(token)
    if not token_data or not token_data.user_id:
        return None

    user = await get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        return None

    return user


async def require_current_user(
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """
    Require an authenticated user (for protected endpoints).

    Raises 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Email or username already exists"},
    },
)
async def register(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new user account.

    Args:
        user_data: Registration data (email, username, password)
        db: Database session

    Returns:
        Created user profile
    """
    # Check if email already exists
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = await get_user_by_username(db, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = await create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Authenticate user and return JWT access token.

    Uses OAuth2 password flow (username field accepts email).

    Args:
        form_data: Login credentials (username=email, password)
        db: Database session

    Returns:
        JWT access token
    """
    # Authenticate user (username field contains email)
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: Annotated[User, Depends(require_current_user)],
):
    """
    Get the currently authenticated user's profile.

    Requires valid JWT token in Authorization header.

    Returns:
        Current user profile
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
