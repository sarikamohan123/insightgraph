"""
API Key Authentication Middleware
===================================

Simple API key authentication for securing mutation endpoints.

Security Model:
- Read-only endpoints (GET): Public (rate-limited)
- Mutation endpoints (POST, PUT, DELETE): Require API key

Usage:
    @app.post("/secure-endpoint", dependencies=[Depends(require_api_key)])
    async def secure_endpoint():
        ...

Configuration:
    Set API_KEY in .env file
"""

from config import settings
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Define API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException(401): If API key is missing or invalid
    """
    # Check if API key is required
    if not settings.api_key:
        # If no API key is configured, allow access (dev mode)
        return "dev-mode"

    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def optional_api_key(api_key: str = Security(api_key_header)) -> str | None:
    """
    Optional API key validation (for endpoints that want to check but not require).

    Returns:
        API key if valid, None otherwise
    """
    if not api_key or not settings.api_key:
        return None

    if api_key == settings.api_key:
        return api_key

    return None
