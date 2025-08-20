
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
    body_bytes = await req.body()

    if not body_bytes:
        return JSONResponse({"ok": True})

    try:
        update: Dict[str, Any] = await req.json()
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return JSONResponse({"ok": False, "error": "Invalid JSON"})

    msg: Optional[Dict[str, Any]] = update.get("message") or update.get("edited_message")
    if not msg:
        return JSONResponse({"ok": True})

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    from_user = msg.get("from") or {}
    user_id = str(from_user.get("id") or chat_id or "anon")
    text = msg.get("text") or ""
    
    print(f"📥 Incoming message from user {user_id} in chat {chat_id}: {text}")
    handled, output = await handle_message(user_id, text, channel="telegram")

    if output and chat_id:
        client = TelegramClient()
        try:
            await client.send_message(chat_id, output, reply_to_message_id=msg.get("message_id"))
            print(f"✅ Sent message to Telegram chat {chat_id}: {output}")
        except Exception as e:
            print(f"--- ERROR SENDING TELEGRAM REPLY ---\n{e}\n-----------------\n")
            print("\n--- Outgoing Telegram Message ---")
            print(f"Chat ID: {chat_id}")
            print(f"Message: {output}")
            

    return JSONResponse({"ok": True, "handled": handled})
