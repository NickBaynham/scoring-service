"""Optional API key authentication."""

from app.core.config import Settings, get_settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    _request: Request,
    settings: Settings = Depends(get_settings),
    api_key: str | None = Depends(api_key_header),
) -> None:
    """Reject requests when API_KEY is configured and the header is missing or wrong."""
    expected = settings.api_key
    if not expected:
        return
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
