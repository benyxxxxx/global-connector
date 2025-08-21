# app/security.py
import os
from typing import Optional
from fastapi import Header, HTTPException

def require_router_secret(
    x_router_secret: Optional[str] = Header(None, convert_underscores=False),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, convert_underscores=False),
) -> None:
    """
    Accepts any of:
      - X-Router-Secret: <token>
      - X-API-Key: <token>
      - Authorization: Bearer <token>

    Tokens allowed:
      - APP_SECRET_KEY (existing admin key)
      - APP_LLM_SECRET  (optional, for your LLM client)
    """
    admin = os.getenv("APP_SECRET_KEY")
    llm = os.getenv("APP_LLM_SECRET")  # optional

    allowed_tokens = [t for t in [admin, llm] if t]

    # development fallback: if no secret is configured, don't block
    if not allowed_tokens:
        return

    presented = []
    if x_router_secret:
        presented.append(x_router_secret)
    if x_api_key:
        presented.append(x_api_key)
    if authorization and authorization.lower().startswith("bearer "):
        presented.append(authorization.split(" ", 1)[1].strip())

    if any(tok in allowed_tokens for tok in presented):
        return

    raise HTTPException(status_code=401, detail="Unauthorized")
