import os
import time
import json
import httpx
import base64
import hmac
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime

# Read configuration from environment variables
BASE = os.getenv("SERVICE_API_BASE", "").rstrip("/")
SECRET_KEY = os.getenv("APP_SECRET_KEY", "")
TIMEOUT = float(os.getenv("SERVICE_API_TIMEOUT", "12"))

def _b64url(data: bytes) -> str:
    """Encodes bytes to base64url format."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _sign_hs256(payload: Dict[str, Any]) -> str:
    """Signs a payload and returns a JWT."""
    if not SECRET_KEY:
        raise RuntimeError("APP_SECRET_KEY is not set in .env file")
        
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url(sig)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def _auth_headers(user_id: Optional[str]) -> Dict[str, str]:
    """Generates the authorization headers for a request."""
    if not BASE:
        raise RuntimeError("SERVICE_API_BASE is not set in .env file")
    
    now = int(time.time())
    token = _sign_hs256({
        "user_id": user_id or "router-service",
        "iat": now,
        "exp": now + 3600
    })
    
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

async def _get(path: str, params: Optional[Dict[str, Any]], user_id: Optional[str]):
    """Makes an authenticated GET request."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as cx:
        headers = _auth_headers(user_id)
        r = await cx.get(f"{BASE}{path}", params=params, headers=headers)
        r.raise_for_status()
        return r.json()

async def _post(path: str, json_body: Dict[str, Any], user_id: Optional[str]):
    """Makes an authenticated POST request."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as cx:
        headers = _auth_headers(user_id)
        json_body['scheduled_at'] = datetime.now().isoformat()
        r = await cx.post(f"{BASE}{path}", json=json_body, headers=headers)
        r.raise_for_status()
        return r.json()

# --- Public API Functions ---

async def list_services(user_id: Optional[str] = None, query: Optional[str] = None):
    """
    Fetches services from the backend. If a query is provided,
    it is passed as a search parameter.
    """
    params = {"q": query} if query else None
    return await _get("/api/services/", params, user_id)

async def create_booking(user_id: str, payload: Dict[str, Any]):
    return await _post("/api/bookings/", payload, user_id)