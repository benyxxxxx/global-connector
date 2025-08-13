
import os, time, json, httpx, base64, hmac, hashlib
from typing import Any, Dict, List, Optional

BASE = os.getenv("SERVICE_API_BASE", "").rstrip("/")
STATIC_JWT = os.getenv("SERVICE_API_JWT", "")
SECRET_KEY = os.getenv("SERVICE_API_SECRET_KEY", "")
TIMEOUT = float(os.getenv("SERVICE_API_TIMEOUT", "12"))

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _sign_hs256(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def _auth_headers(user_id: Optional[str]) -> Dict[str, str]:
    if not BASE:
        raise RuntimeError("SERVICE_API_BASE not set")
    if STATIC_JWT:
        return {"Authorization": f"Bearer {STATIC_JWT}", "Accept": "application/json"}
    if SECRET_KEY:
        now = int(time.time())
        token = _sign_hs256({"sub": user_id or "router", "iat": now, "exp": now + 3600})
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    return {"Accept": "application/json"}

async def _get(path: str, params: Optional[Dict[str, Any]], user_id: Optional[str]):
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=_auth_headers(user_id)) as cx:
        r = await cx.get(f"{BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()

async def _post(path: str, json_body: Dict[str, Any], user_id: Optional[str]):
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=_auth_headers(user_id)) as cx:
        r = await cx.post(f"{BASE}{path}", json=json_body)
        r.raise_for_status()
        return r.json()

# ---- endpoints ----
async def list_services(channel_id: Optional[str] = None, user_id: Optional[str] = None):
    params = {"channel_id": str(channel_id)} if channel_id else None
    return await _get("/api/services/", params, user_id)

async def get_service(service_id: int, user_id: Optional[str] = None):
    return await _get(f"/api/services/{service_id}", None, user_id)

async def get_memory(user_id: str):
    return await _get("/api/memory/", {"user_id": user_id}, user_id)

async def save_memory(user_id: str, text: str):
    return await _post("/api/memory/", {"user_id": user_id, "text": text}, user_id)

async def create_booking(user_id: str, payload: Dict[str, Any]):
    return await _post("/api/bookings/", {"user_id": user_id, **payload}, user_id)
