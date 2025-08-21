from __future__ import annotations
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.agents.service_agent import handle_message
from app.integrations.telegram import TelegramClient
from app.core import session_store as sess
from app.core import agent_manager as agents_mgr

router = APIRouter()  # keep original mounting so path stays /telegram/webhook

WEBHOOK_SECRET   = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
DEFAULT_AGENT_ID = os.getenv("DEFAULT_AGENT_ID")  # optional default agent id



@router.post("/telegram/webhook")
async def telegram_webhook(req: Request) -> JSONResponse:
    # Optional: verify Telegram secret header (set when you call setWebhook)
    if WEBHOOK_SECRET:
        if req.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

    body_bytes = await req.body()
    if not body_bytes:
        return JSONResponse({"ok": True})

    try:
        update: Dict[str, Any] = await req.json()
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)

    msg: Optional[Dict[str, Any]] = update.get("message") or update.get("edited_message")
    if not msg:
        return JSONResponse({"ok": True})

    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    from_user = msg.get("from") or {}
    user_id = str(from_user.get("id") or chat_id or "anon")
    text = (msg.get("text") or "").strip()

    print(f"📥 Incoming message from user {user_id} in chat {chat_id}: {text}")

    # Resolve active agent for this chat (fallback to DEFAULT_AGENT_ID if set)
    active_agent_id = (sess.get_active(str(chat_id)) if chat_id is not None else None) or DEFAULT_AGENT_ID

    client = TelegramClient()

    # --- bot commands (lightweight, no conflict) ---
    if text.startswith("/agent") or text.startswith("/whoami"):
        name = active_agent_id or "(none)"
        await client.send_message(chat_id, f"Active agent: {name}", reply_to_message_id=msg.get("message_id"))
        return JSONResponse({"ok": True})

    if text.startswith("/agents"):
        items = agents_mgr.list_agents(include_archived=False)
        public = [a for a in items if a.visibility in ("public", "unlisted")]
        if not public:
            await client.send_message(chat_id, "No public agents yet.", reply_to_message_id=msg.get("message_id"))
        else:
            lines = [f"- {a.name} ({a.id})" for a in public[:20]]
            await client.send_message(chat_id, "Available agents:\n" + "\n".join(lines), reply_to_message_id=msg.get("message_id"))
        return JSONResponse({"ok": True})

    if text.startswith("/use "):
        token = text.split(" ", 1)[1].strip()
        target = next((a for a in agents_mgr.list_agents(False) if a.id == token or a.name == token), None)
        if not target:
            await client.send_message(chat_id, "Agent not found. Use /agents to list.", reply_to_message_id=msg.get("message_id"))
            return JSONResponse({"ok": True})
        sess.set_active(str(chat_id), target.id)
        await client.send_message(chat_id, f"✅ Now using: {target.name} ({target.id})", reply_to_message_id=msg.get("message_id"))
        return JSONResponse({"ok": True})

    if text.startswith("/clear"):
        sess.clear_active(str(chat_id))
        await client.send_message(chat_id, "Cleared agent for this chat.", reply_to_message_id=msg.get("message_id"))
        return JSONResponse({"ok": True})

    # Optional: log incoming message to the agent’s brain (audit trail)
    if active_agent_id and text:
        try:
            agents_mgr.log_message(active_agent_id, f"TG[{chat_id}]: {text}", user_id=str(chat_id), tag="msg")
        except Exception as e:
            print("log_message failed:", e)

    # Call your existing handler (keeps previous behavior)
    try:
        handled, output = await handle_message(user_id=user_id, text=text, channel="telegram")
    except TypeError:
        # if legacy signature without keywords:
        handled, output = await handle_message(user_id, text, "telegram")

    # Send reply via your Telegram client
    if output and chat_id:
        try:
            await client.send_message(chat_id, output, reply_to_message_id=msg.get("message_id"))
            print(f"✅ Sent message to Telegram chat {chat_id}: {output}")
        except Exception as e:
            print(f"--- ERROR SENDING TELEGRAM REPLY ---\n{e}\n-----------------\n")
            print("\n--- Outgoing Telegram Message ---")
            print(f"Chat ID: {chat_id}")
            print(f"Message: {output}")

    return JSONResponse({"ok": True, "handled": bool(handled)})
