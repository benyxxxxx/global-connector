# app/routes/telegram_webhook.py
from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, Optional


import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
# --- your existing imports (kept) ---
from app.agents.service_agent import handle_message
from app.integrations.telegram import TelegramClient
from app.core import session_store as sess
from app.core import agent_manager as agents_mgr
from app.models.agent_pydantic_models import AgentCreateRequest
from app.services import router_service as ROUTER
from app.agents import info_only_agent as INFO
from app.clients import backend_api as be  # used for category list
from app.services.github_service import trigger_deployment_workflow
from app.clients import backend_api as be  # used for category list
from app.services.github_service import trigger_deployment_workflow

router = APIRouter()

# --- existing envs (kept) ---
# --- existing envs (kept) ---
WEBHOOK_SECRET   = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
DEFAULT_AGENT_ID = os.getenv("DEFAULT_AGENT_ID")

# --- NEW: envs required for webhook ZIP + promote bridge ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()  # BotFather token
INTEGRATOR_BASE_URL = os.getenv("INTEGRATOR_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
ADMIN_HEADER_NAME = "X-Integrator-Admin"
ADMIN_HEADER_VALUE = os.getenv("PROMOTE_ADMIN_TOKEN", "").strip()
MAX_ZIP_BYTES = 60 * 1024 * 1024  # 60 MB

ADMIN_IDS = [int(i) for i in os.environ.get("BOT_ADMIN_IDS", "").split(",") if i]

def _tg_api(method: str) -> str:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN env var is required for Telegram webhook file handling")
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"


@router.post("/telegram/webhook")
async def telegram_webhook(req: Request) -> JSONResponse:
    """
    Telegram webhook:
      • If message has a ZIP (document) → download from Telegram → POST to Stage-A.
      • If message is `/promote stage-a/<branch>` → POST to Stage-B.
      • Else: fall back to your existing menu/agent/session logic.
    """
    
    chat_id: Optional[str] = None
    """
    Telegram webhook:
      • If message has a ZIP (document) → download from Telegram → POST to Stage-A.
      • If message is `/promote stage-a/<branch>` → POST to Stage-B.
      • Else: fall back to your existing menu/agent/session logic.
    """
    
    chat_id: Optional[str] = None
    output = ""


    try:
        # Optional: verify secret header (Telegram will send X-Telegram-Bot-Api-Secret-Token if you set it)
        # Optional: verify secret header (Telegram will send X-Telegram-Bot-Api-Secret-Token if you set it)
        if WEBHOOK_SECRET:
            if req.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
                return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)

        body = await req.body()
        if not body:
            return JSONResponse({"ok": True, "info": "empty_request"})
        
        update: Dict[str, Any] = json.loads(body)
        client = TelegramClient()

        # --- Handle callback_query (unchanged flow) ---

        # --- Handle callback_query (unchanged flow) ---
        if "callback_query" in update:
            callback_query = update["callback_query"]
            chat_id = str(callback_query["message"]["chat"]["id"])
            user_id = str(callback_query["from"]["id"])
            data = callback_query["data"]
            msg = callback_query["message"]

            # best-effort ack

            # best-effort ack
            try:
                await client.answer_callback_query(callback_query["id"])
            except Exception:
                pass

            # let your info-only agent handle inline callbacks first

            # let your info-only agent handle inline callbacks first
            info_cb = await INFO.handle_callback(str(chat_id), user_id, data, client)
            if info_cb and info_cb.get("handled"):
                if info_cb.get("output"):
                    await client.send_message(chat_id, info_cb["output"])
                return JSONResponse({"ok": True})

            # if not handled, treat callback data as a text command

            # if not handled, treat callback data as a text command
            text = data

            # quick promote path from inline callback (optional)
            if text.lower().startswith("/promote "):
                branch = text.split(" ", 1)[1].strip()
                return await _do_promote(branch, chat_id, client)

            # otherwise fall through to the standard text handling below

        # --- Regular message / edited_message ---
        msg: Optional[Dict[str, Any]] = update.get("message") or update.get("edited_message")
        if not msg:
            return JSONResponse({"ok": True})

        chat = msg.get("chat", {}) or {}
        chat_id = str(chat.get("id"))
        from_user = msg.get("from", {}) or {}
        user_id = str(from_user.get("id") or chat_id or "anon")

        # === 1) DOCUMENT (ZIP) HANDLING ===
        doc = msg.get("document")
        if doc:
            # Validate .zip + size
            name = (doc.get("file_name") or "").lower()
            if not name.endswith((".zip", ".patch", ".diff", ".yaml", ".yml", ".json")):
                print(f"❌ Rejected file from {user_id}: {name}")
                await client.send_message(chat_id, "❌ File ignored. Must be a .zip, .patch, .diff, .yaml, or .json file.")
                return JSONResponse({"ok": True})
            size = int(doc.get("file_size") or 0)
            if size and size > MAX_ZIP_BYTES:
                await client.send_message(chat_id, "❌ ZIP too large (max 60 MB).")
                return JSONResponse({"ok": True})

            if not BOT_TOKEN:
                await client.send_message(chat_id, "❌ BOT_TOKEN is not configured on the server.")
                return JSONResponse({"ok": True})

            # 1) get Telegram file path
            async with httpx.AsyncClient(timeout=15.0) as hc:
                r = await hc.get(_tg_api("getFile"), params={"file_id": doc["file_id"]})
                r.raise_for_status()
                j = r.json()
                if not j.get("ok"):
                    await client.send_message(chat_id, "❌ Failed to fetch file path.")
                    return JSONResponse({"ok": True})
                file_path = j["result"]["file_path"]

            # 2) download bytes
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            async with httpx.AsyncClient(timeout=180.0) as hc2:
                r2 = await hc2.get(file_url)
                r2.raise_for_status()
                zip_bytes = r2.content
            if len(zip_bytes) > MAX_ZIP_BYTES:
                await client.send_message(chat_id, "❌ ZIP too large (max 60 MB).")
                return JSONResponse({"ok": True})

            # 3) forward to correct endpoint based on file type
            title = f"tg-{from_user.get('username') or 'user'}-{int(time.time())}"
            headers = {ADMIN_HEADER_NAME: ADMIN_HEADER_VALUE} if ADMIN_HEADER_VALUE else {}
            data = {"title": title}

            # --- PATCH/DIFF HANDLING ---
            if name.endswith((".patch", ".diff")):
                files = {"file": (name, zip_bytes, "text/plain")}  # Use key "file"
                
                async with httpx.AsyncClient(timeout=180.0) as hc3:
                    resp = await hc3.post(
                        f"{INTEGRATOR_BASE_URL}/integrations/stage-d/submit-patch", # Correct endpoint
                        files=files,
                        data=data,
                        headers=headers,
                    )
                    if resp.status_code < 300:
                        out = resp.json()
                        branch = out.get("branch", "(unknown)")
                        await client.send_message(chat_id, f"✅ Stage D patch applied\nBranch: {branch}")
                    else:
                        error_details = resp.text
                        await client.send_message(chat_id, f"❌ Stage D error {resp.status_code}.\nDetails: {error_details}")
                return JSONResponse({"ok": True})

            # --- ZIP HANDLING ---
            if name.endswith(".zip"):
                files = {"upload": (name, zip_bytes, "application/zip")} # Use key "upload"
                
                async with httpx.AsyncClient(timeout=180.0) as hc3:
                    resp = await hc3.post(
                        f"{INTEGRATOR_BASE_URL}/integrations/stage-a/submit-zip", # Original endpoint
                        files=files,
                        data=data,
                        headers=headers,
                    )
                    if resp.status_code < 300:
                        out = resp.json()
                        branch = out.get("branch", "(unknown)")
                        await client.send_message(chat_id, f"✅ Stage A uploaded\nBranch: {branch}")
                    else:
                        # error is coming form here
                        await client.send_message(chat_id, f"❌ Stage A and error {resp.status_code}.")
                return JSONResponse({"ok": True})

        # === 2) TEXT COMMANDS & DIALOG FLOW ===
        text = (msg.get("text") or "").strip()
        if text.lower().startswith("/resetbot"):
            # if user_id not in ADMIN_IDS: # <--- THIS LINE IS COMMENTED OUT
            #     await client.send_message(chat_id, "🚫 You are not authorized for this command.")
            #     return JSONResponse({"ok": True})
            
            args = text.split(maxsplit=1)
            fly_config = args[1] if len(args) > 1 else "fly.test.toml"

            await client.send_message(chat_id, f"🚀 Triggering deployment with `{fly_config}`...")
            run_url = await trigger_deployment_workflow(fly_config=fly_config)

            if run_url:
                await client.send_message(chat_id, f"✅ Workflow started. Track progress here:\n{run_url}", disable_web_page_preview=True)
            else:
                await client.send_message(chat_id, "❌ Failed to trigger deployment. Check bot logs.")
            
            return JSONResponse({"ok": True})
        # === 2) TEXT COMMANDS & DIALOG FLOW ===
        text = (msg.get("text") or "").strip()
        if text.lower().startswith("/resetbot"):
            # if user_id not in ADMIN_IDS: # <--- THIS LINE IS COMMENTED OUT
            #     await client.send_message(chat_id, "🚫 You are not authorized for this command.")
            #     return JSONResponse({"ok": True})
            
            args = text.split(maxsplit=1)
            fly_config = args[1] if len(args) > 1 else "fly.test.toml"

            await client.send_message(chat_id, f"🚀 Triggering deployment with `{fly_config}`...")
            run_url = await trigger_deployment_workflow(fly_config=fly_config)

            if run_url:
                await client.send_message(chat_id, f"✅ Workflow started. Track progress here:\n{run_url}", disable_web_page_preview=True)
            else:
                await client.send_message(chat_id, "❌ Failed to trigger deployment. Check bot logs.")
            
            return JSONResponse({"ok": True})

        print(f"📥 Incoming message from user {user_id} in chat {chat_id}: {text}")

        # Fast path: /promote stage-a/<branch>
        if text.lower().startswith("/promote "):
            branch = text.split(" ", 1)[1].strip()
            return await _do_promote(branch, chat_id, client)

        # If we're in a router "create service" flow
        # Fast path: /promote stage-a/<branch>
        if text.lower().startswith("/promote "):
            branch = text.split(" ", 1)[1].strip()
            return await _do_promote(branch, chat_id, client)

        # If we're in a router "create service" flow
        session = sess.get_session(chat_id)
        state = session.get("state")
        if state and state.startswith("svc_create_"):
            resp = await ROUTER.handle_agent_message(chat_id, user_id, text)
            await client.send_message(chat_id, resp["reply"])
            return JSONResponse({"ok": True})

        # Slash-commands & categories
        if text.startswith("/"):
            # Dynamic category commands (e.g., /food, /tech) → info-only browsing
            try:
                available_categories = await be.get_non_empty_categories_async()
            except Exception:
                available_categories = []
            normalized = [c.lower() for c in available_categories]
            cmd = text[1:].strip().lower()
            if cmd in normalized:
                info_resp = await INFO.handle_message(chat_id, cmd, client)
                if info_resp and info_resp.get("output"):
                    await client.send_message(chat_id, info_resp["output"], reply_to_message_id=msg.get("message_id"))
                return JSONResponse({"ok": True})

            # Menu / discovery

            # Menu / discovery
            if (
                text in {"/menu", "/start"} or
                re.search(r"\b(menu|categories|what do you have|what services do you have)\b", text, re.I) or
                re.search(r"\b(food|restaurant|restaurants|dining|transport|taxi|bike|bicycle|scooter)\b", text, re.I)
            ):
                info_resp = await INFO.handle_message(chat_id, text, client)
                if info_resp and info_resp.get("output"):
                    await client.send_message(chat_id, info_resp["output"], reply_to_message_id=msg.get("message_id"))
                return JSONResponse({"ok": True})

            # Begin create-service via command
            if text in {"/add_service", "/add", "/service_add", "/new"} or re.search(r"\b(add|create|new)\s*service", text, re.I):
                resp = await ROUTER.handle_agent_message(chat_id, user_id, text)
                await client.send_message(chat_id, resp["reply"])
                return JSONResponse({"ok": True})

            # Agent creation wizard
            if text.startswith("/create"):
                sess.update_session(chat_id, {"state": "create_name", "form_data": {}})
                await client.send_message(chat_id, "🆕 **Create a New Agent**\n\nEnter a name for your agent:")
                return JSONResponse({"ok": True})

            if text.startswith("/agents"):
                items = agents_mgr.list_agents(include_archived=False)
                public = [a for a in items if a.visibility in ("public", "unlisted")]
                if not public:
                    await client.send_message(chat_id, "There are no public agents available at the moment.")
                    return JSONResponse({"ok": True})

                keyboard = []
                for i in range(0, len(public), 2):
                    row = [{"text": f"{public[i].name}", "callback_data": f"/use {public[i].id}"}]
                    if i + 1 < len(public):
                        row.append({"text": f"{public[i+1].name}", "callback_data": f"/use {public[i+1].id}"})
                    keyboard.append(row)

                reply_markup = {"inline_keyboard": keyboard}
                await client.send_message(chat_id, "Please choose a bot to interact with:", reply_markup=reply_markup)
                return JSONResponse({"ok": True})

            if text.startswith("/agent") or text.startswith("/whoami"):
                active_agent_id = sess.get_active(chat_id) or DEFAULT_AGENT_ID
                name = active_agent_id or "(none)"
                await client.send_message(chat_id, f"Active agent: {name}", reply_to_message_id=msg.get("message_id"))
                return JSONResponse({"ok": True})

            if text.startswith("/use "):
                token = text.split(" ", 1)[1].strip()
                target = next((a for a in agents_mgr.list_agents(False) if a.id == token or a.name == token), None)
                if not target:
                    await client.send_message(chat_id, "Agent not found. Use /agents to list.", reply_to_message_id=msg.get("message_id"))
                else:
                    sess.set_active(chat_id, target.id)
                    await client.send_message(chat_id, f"✅ Now using: {target.name} ({target.id})", reply_to_message_id=msg.get("message_id"))
                return JSONResponse({"ok": True})

            if text.startswith("/clear"):
                sess.clear_active(chat_id)
                await client.send_message(chat_id, "Cleared agent for this chat.", reply_to_message_id=msg.get("message_id"))
                return JSONResponse({"ok": True})

        # Plain-text create-service intent
        if re.search(r"\b(add|create|new)\s*service", text, re.I):
            resp = await ROUTER.handle_agent_message(chat_id, user_id, text)
            await client.send_message(chat_id, resp["reply"])
            return JSONResponse({"ok": True})

        # Agent creation wizard (multi-step)
        session = sess.get_session(chat_id)
        state = session.get("state")
        if state == "create_name":
            session["form_data"] = {"name": text}
            session["state"] = "create_description"
            sess.update_session(chat_id, session)
            await client.send_message(chat_id, "📝 Enter agent description:")
            return JSONResponse({"ok": True})

        if state == "create_description":
            session["form_data"]["description"] = text
            session["state"] = "create_visibility"
            sess.update_session(chat_id, session)
            await client.send_message(chat_id, "🔒 Set visibility: `public`, `unlisted`, or `private`?")
            return JSONResponse({"ok": True})

        if state == "create_visibility":
            visibility = text.lower()
            if visibility not in ["public", "unlisted", "private"]:
                await client.send_message(chat_id, "❌ Invalid. Please enter `public`, `unlisted`, or `private`.")
                return JSONResponse({"ok": True})
            session["form_data"]["visibility"] = visibility
            create_req = AgentCreateRequest(**session["form_data"])
            agent = agents_mgr.create_agent(create_req)
            await client.send_message(
                chat_id,
                f"✅ Agent '{agent.name}' created and your Agent_id is `{agent.id}`.",
                reply_to_message_id=msg.get("message_id"),
            )
            sess.clear_session_state(chat_id)
            return JSONResponse({"ok": True})

        # Default: chat with active agent
        active_agent_id = sess.get_active(chat_id)
        if not active_agent_id:
            # Try getting agent by ID first, then by name.
            agent = agents_mgr.get_agent(DEFAULT_AGENT_ID)
            if agent:
                active_agent_id = agent.id
            else:
                agents = agents_mgr.list_agents()
                for a in agents:
                    if a.name == DEFAULT_AGENT_ID:
                        active_agent_id = a.id
                        break
        
        if not active_agent_id:
            await client.send_message(
                chat_id,
                "Hello! How can I assist you today? If you're looking for services to book, just let me know!"
            )
            return JSONResponse({"ok": True})

        if text:
            agents_mgr.log_message(active_agent_id, f"TG[{chat_id}]: {text}", user_id=user_id, tag="msg")

        handled, output = await handle_message(user_id=user_id, text=text, channel="telegram")
        if output:
            success = await client.send_message(chat_id, output, reply_to_message_id=msg.get("message_id"))
            if success:
                print(f"✅ Sent message to Telegram chat {chat_id}: {output}")

        return JSONResponse({"ok": True, "handled": bool(handled)})

    except httpx.ConnectError as e:
        # Network to Telegram or your API failed; don't break webhook delivery
        print(f"--- ConnectError ---\n{e}\n-----------------")
        return JSONResponse({"ok": True, "error_handled": "ConnectError"})

    except Exception as e:
        import traceback
        print(f"--- Unexpected error --- {e}")
        traceback.print_exc()
        # attempt best-effort user notification
        try:
            update = await req.json()
            msg_inner = update.get("message", {}) or update.get("callback_query", {}).get("message", {})
            chat_id_inner = msg_inner.get("chat", {}).get("id")
            if chat_id_inner:
                error_client = TelegramClient()
                await error_client.send_message(chat_id_inner, "Sorry, I encountered an error and couldn't process your request.")
        except Exception:
            pass
        return JSONResponse({"ok": True, "error_handled": True})


# --- helpers ---

async def _do_promote(branch: str, chat_id: str, client: TelegramClient) -> JSONResponse:
    """POST /integrations/stage-b/promote and report result to Telegram."""
    if not re.match(r"^stage-a/[a-z0-9._/-]{1,60}$", branch):
        await client.send_message(chat_id, "❌ Invalid branch. Expected: stage-a/<slug>")
        return JSONResponse({"ok": True})

    headers = {ADMIN_HEADER_NAME: ADMIN_HEADER_VALUE} if ADMIN_HEADER_VALUE else {}
    try:
        async with httpx.AsyncClient(timeout=90.0) as hc:
            r = await hc.post(
                f"{INTEGRATOR_BASE_URL}/integrations/stage-b/promote",
                json={"branch": branch},
                headers=headers,
            )
            if r.status_code < 300:
                j = r.json()
                await client.send_message(
                    chat_id,
                    "✅ Promoted\n"
                    f"PR: #{j.get('pr_number')} | Tag: {j.get('tag')}\n"
                    f"SHA: {j.get('sha')}\n{j.get('pr_url') or ''}".strip()
                )
            else:
                await client.send_message(chat_id, f"❌ Promote error {r.status_code}.")
    except Exception as e:
        print("Promote failed:", e)
        await client.send_message(chat_id, "❌ Promote failed. Please try again.")
    return JSONResponse({"ok": True})