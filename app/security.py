import os
from fastapi import Request, HTTPException, status, Security
from fastapi.security import APIKeyHeader

# Read the single secret key from the .env file
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "").strip()

# Define the security scheme for Swagger UI
api_key_header = APIKeyHeader(name="X-Router-Secret", auto_error=False)

async def require_router_secret(api_key: str = Security(api_key_header)) -> None:
    """
    This dependency checks for the X-Router-Secret header and validates it.
    It is now integrated with Swagger UI.
    """
    if not APP_SECRET_KEY:
        # If no key is set, allow the request
        return

    if not api_key or api_key.strip() != APP_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Router-Secret header.",
        )