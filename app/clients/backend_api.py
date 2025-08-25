import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

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
        # The agent provides scheduled_at, so we remove the automatic addition here.
        r = await cx.post(f"{BASE}{path}", json=json_body, headers=headers)
        r.raise_for_status()
        return r.json()


async def list_services(user_id: Optional[str] = None, query: Optional[str] = None):
    """
    Fetches services from the backend. If a query is provided,
    it is passed as a search parameter.
    """
    params = {"q": query} if query else None
    return await _get("/api/services/", params, user_id)

async def list_categories(user_id: Optional[str] = None):
    """
    Fetch service categories. If the endpoint is missing, fall back to deriving categories from services.
    Returns a dict like {"categories": [{"name": "<category>"}, ...]} for consistency.
    """
    try:
        data = await _get("/api/service-categories/", None, user_id)
        # normalize format
        if isinstance(data, dict) and "categories" in data:
            return data
        if isinstance(data, list):
            return {"categories": data}
    except Exception:
        pass
    # Fallback: derive from services
    try:
        services = await _get("/api/services/", None, user_id) or []
        if isinstance(services, dict) and "results" in services:
            services = services["results"]
        names = sorted({(svc.get("category") or svc.get("type") or "").strip()
                        for svc in services if isinstance(svc, dict) and (svc.get("category") or svc.get("type"))})
        return {"categories": [{"name": n} for n in names if n]}
    except Exception as e:
        return {"error": str(e)}

async def create_booking(user_id: str, service_id: str, full_name: str, scheduled_at: str, duration: Optional[int] = None):
    """Creates a booking by sending data to the backend."""
    payload = {
        "service_id": service_id,
        "full_name": full_name,
        "scheduled_at": scheduled_at,
    }
    if duration:
        payload["duration"] = duration
    
    return await _post("/api/bookings/", payload, user_id)

