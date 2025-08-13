from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from typing import Any, Dict

from app.agents.service_agent import handle_message
from app.security import require_router_secret

router = APIRouter()

@router.post("/route")
async def route_endpoint(
    body: Dict[str, Any],
    req: Request,
    _=Depends(require_router_secret)  # Enforces X-Router-Secret check
) -> JSONResponse:
    """
    Handles incoming messages via the /route endpoint.
    Requires X-Router-Secret header for authorization.
    """

    # Extract user_id and message safely
    user_id = str(body.get("user_id", "anon"))
    text = str(body.get("message", "") or "")

    # Process the message using your agent
    handled, output = await handle_message(user_id, text, channel="http")

    return JSONResponse({"handled": handled, "output": output})
