
import asyncio
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from app.security import require_router_secret
from app.agents.service_agent import handle_message
from app.integrations.telegram import TelegramClient

router = APIRouter()

@router.post("/telegram/webhook")
async def telegram_webhook(req: Request) -> JSONResponse:
    update: Dict[str, Any] = await req.json()
    msg: Optional[Dict[str, Any]] = update.get("message") or update.get("edited_message")
    if not msg:
        return JSONResponse({"ok": True})

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    from_user = msg.get("from") or {}
    user_id = str(from_user.get("id") or chat_id or "anon")
    text = msg.get("text") or ""

    handled, output = await handle_message(user_id, text, channel="telegram")

    if output and chat_id:
        client = TelegramClient()
        async def safe_send():
            try:
                await client.send_message(chat_id, output, reply_to_message_id=msg.get("message_id"))
            except Exception:
                pass
        asyncio.create_task(safe_send())

    return JSONResponse({"ok": True, "handled": handled})
