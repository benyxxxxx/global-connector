import os
from typing import Optional
import re
import unicodedata
import json
import asyncio
import time
from app.core import session_store as sess

import inspect

from app.agents import service_agent as SA
from app.clients import backend_api as be

# ⬇️ import your existing bits
# from app.orchestrator.runtime import run_orchestrator  # <- your function that talks to LLM + tools
# from app.db import SessionLocal
# from app.models import Agent, Session, AgentMemory  # rename to your actual models

DEFAULT_AGENT_ID = os.getenv("DEFAULT_AGENT_ID", "agent_service")
def _normalize_text(t: str) -> str:
    """
    Normalize message variants so 'AddService', 'add_service', 'add-service'
    all become 'add service'; also NFKC unicode normalize and lowercase.
    """
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)   # split CamelCase (AddService -> Add Service)
    t = re.sub(r'[_\-]+', ' ', t)                # underscores/dashes -> space
    t = re.sub(r'\s+', ' ', t).strip().lower()   # squeeze spaces + lowercase
    return t

# --- Agent repo (DB-backed) ---
def list_agents(db) -> list[dict]:
    # return public/unlisted as your API expects
    # rows = db.query(Agent).filter(Agent.is_archived == False).all()
    # return [row.to_dict() for row in rows]
    ...

def get_agent(db, agent_id: str) -> Optional[dict]:
    # a = db.query(Agent).filter(Agent.id == agent_id).first()
    # return a.to_dict() if a else None
    ...

def create_agent(db, data: dict) -> dict:
    # a = Agent(**data); db.add(a); db.commit(); db.refresh(a); return a.to_dict()
    ...

def update_agent(db, agent_id: str, data: dict) -> dict:
    # a = db.query(Agent).filter(Agent.id == agent_id).first(); update fields; db.commit(); return a.to_dict()
    ...

def archive_agent(db, agent_id: str) -> None:
    # a.is_archived = True; db.commit()
    ...

def ensure_seed_agent(db):
    # if not exists(DEFAULT_AGENT_ID): create a minimal default
    # if not db.query(Agent).filter(Agent.id == DEFAULT_AGENT_ID).first():
    #     db.add(Agent(id=DEFAULT_AGENT_ID, name="Service Agent", public=True))
    #     db.commit()
    ...

# --- Session repo (DB-backed) ---
def get_active_agent(db, chat_id: str) -> str | None:
    # s = db.query(Session).filter(Session.chat_id == chat_id).first()
    # return s.agent_id if s else None
    ...

def set_active_agent(db, chat_id: str, agent_id: str) -> None:
    # upsert in your Session table
    ...

# --- Memory repo (DB-backed) ---
def add_memory(db, agent_id: str, chat_id: str, role: str, text: str):
    # db.add(AgentMemory(agent_id=agent_id, chat_id=chat_id, role=role, text=text)); db.commit()
    ...

# --- Runtime wrapper (uniform response) ---
async def handle_agent_message(chat_id: str, user_id: str, text: str, agent_id: Optional[str] = None) -> dict:
    agent_id = agent_id or DEFAULT_AGENT_ID
    t_raw = (text or "").strip()          # <-- define raw text
    t_norm = _normalize_text(t_raw)       # normalized (underscores -> spaces, lowercase)

    # --- session (same store as /create agent flow)
    session = sess.get_session(chat_id)
    state = session.get("state")
    form = session.get("svc_form", {})

    # ========== Cancel ==========
    if state and state.startswith("svc_create_") and t_norm in {"cancel", "/cancel"}:
        sess.clear_session_state(chat_id)
        return {
            "handled": True,
            "reply": "Cancelled the add-service flow. Type `/add_service` to start again.",
            "meta": {"agent_id": agent_id, "intent": "cancel_add_service"},
        }

    # ========== Continue Wizard ==========
    if state == "svc_create_business":
        form = {"business_name": t_raw}
        sess.update_session(chat_id, {"state": "svc_create_name", "svc_form": form})
        return {"handled": True, "reply": "What’s the **Service Name**?", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_name":
        form["name"] = t_raw
        sess.update_session(chat_id, {"state": "svc_create_description", "svc_form": form})
        return {"handled": True, "reply": "Add a short **Description**.", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_description":
        form["description"] = t_raw
        sess.update_session(chat_id, {"state": "svc_create_category", "svc_form": form})
        return {"handled": True, "reply": "Which **Category**? (e.g., food, tech)", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_category":
        form["category_name"] = t_raw
        sess.update_session(chat_id, {"state": "svc_create_pricing_model", "svc_form": form})
        return {"handled": True, "reply": "Choose **Pricing Model**: `flat` or `time-based`.", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_pricing_model":
        pm = t_norm
        if pm not in {"flat", "time based", "time-based"}:
            return {"handled": True, "reply": "Please enter `flat` or `time-based`.", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}
        # store to match backend schema (underscore)
        form["pricing_model"] = "time_based" if "time" in pm else "flat"
        sess.update_session(chat_id, {"state": "svc_create_currency", "svc_form": form})
        return {"handled": True, "reply": "Currency code? (e.g., **USD**, **NPR**)", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_currency":
        form["currency"] = t_raw.strip().upper()
        sess.update_session(chat_id, {"state": "svc_create_price", "svc_form": form})
        return {"handled": True, "reply": "What’s the **Base Price**? (number)", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    if state == "svc_create_price":
        price = t_raw.replace(",", "").strip()
        try:
            float(price)
        except Exception:
            return {"handled": True, "reply": "Please enter a valid number for Base Price.", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}
        form["base_price"] = price

        # Submit directly to backend API (same one the orchestrator uses)
        try:
            result = be.create_service(user_id=user_id, **form)   # may be sync or async
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            sess.clear_session_state(chat_id)
            return {"handled": True,
                    "reply": f"Something went wrong creating the service: {e}",
                    "meta": {"agent_id": agent_id, "intent": "add_service", "error": str(e)}}
            

        # Clear state and confirm
        sess.clear_session_state(chat_id)
        human = result if isinstance(result, str) else "Service created."
        return {
            "handled": True,
            "reply": human,
            "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "submit"},
        }


    # ========== Start Wizard (NO '/create' here) ==========
    # Check RAW slash commands first (normalization would break underscores)
    if t_raw in {"/add_service", "/add", "/service_add", "/new"}:
        sess.update_session(chat_id, {"state": "svc_create_business", "svc_form": {}})
        return {
            "handled": True,
            "reply": "Let’s add a new service. What’s the **Business Name**?",
            "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"},
        }

    # Then check normalized phrases / glued variants
    add_re = re.compile(r"\b(add|create|new)\s*(service|services)\b", re.IGNORECASE)
    add_glue_re = re.compile(r"\b(add|create)(service|services)\b", re.IGNORECASE)
    if add_re.search(t_norm) or add_glue_re.search(t_norm):
        sess.update_session(chat_id, {"state": "svc_create_business", "svc_form": {}})
        return {"handled": True, "reply": "Let’s add a new service. What’s the **Business Name**?", "meta": {"agent_id": agent_id, "intent": "add_service", "mode": "guided"}}

    # ========== Fallback (browse/search or LLM) ==========
    loop = asyncio.new_event_loop()
    try:
        handled, answer = loop.run_until_complete(SA.handle_message(user_id=user_id, text=t_raw, channel="http"))
    except Exception as e:
        try: loop.close()
        except Exception: pass
        return {"handled": True, "reply": f"[router_service error] {str(e)}", "meta": {"agent_id": agent_id, "error": str(e)}}
    try: loop.close()
    except Exception: pass

    return {"handled": bool(handled), "reply": answer or "", "meta": {"agent_id": agent_id, "mode": "llm"}}
