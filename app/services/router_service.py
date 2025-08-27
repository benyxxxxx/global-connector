import os
from typing import Optional
import re
import unicodedata

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
def handle_agent_message(chat_id: str, user_id: str, text: str, agent_id: Optional[str] = None) -> dict:
    """Entry called by /router/agent/message.

    Behavior:
      - If `text` is a JSON action (add/update/delete), return an ACK (no DB changes here).
      - Else if text expresses "add service" intent (incl. variants), start guided add flow.
      - Otherwise, delegate to Service Agent LLM orchestration (async-safe).

    Returns: {"handled": bool, "reply": str, "meta": {...}}
    """
    import json

    agent_id = agent_id or DEFAULT_AGENT_ID

    # Try to parse JSON commands like: {"action":"add","target":"...","data":{...}}
    def _try_parse_json(s: str):
        try:
            return json.loads(s)
        except Exception:
            return None

    t = (text or "").strip()

    # -------------------------
    # 1) JSON ACTION — TOP PRIORITY (unchanged behavior)
    # -------------------------
    j = _try_parse_json(t)
    if isinstance(j, dict) and j.get("action") in {"add", "update", "delete"}:
        # Wire these to your DB/service layer later as needed.
        return {
            "handled": True,
            "reply": f"[ack:{j.get('action')}] {j.get('target') or ''}".strip(),
            "meta": {"agent_id": agent_id, "mode": "json-action", "input": j},
        }

    # -------------------------
    # 2) ADD-SERVICE INTENT — prioritized over generic "services"
    # -------------------------
    t_norm = _normalize_text(t)

    # Accept variants: "add service", "add services", "create service", "new service",
    # glued/underscore/dash: "AddService", "add_services", "add-service", "addservices"
    # Short commands: "/add" (optionally "/new" — remove if you don't want it)
    add_re = re.compile(r"\b(add|create|new)\s*(service|services)\b", re.IGNORECASE)
    add_glue_re = re.compile(r"\baddservice(s)?\b", re.IGNORECASE)

    # If you want to EXCLUDE '/new', remove it from the set below.
    if add_re.search(t_norm) or add_glue_re.search(t_norm) or t_norm in {"/add", "/service_add", "/new"}:
        reply = (
            "Let's add a new service!\n\n"
            "**Send JSON** like:\n"
            "```json\n"
            "{\n"
            "  \"action\": \"add\",\n"
            "  \"name\": \"EcoBike Delivery\",\n"
            "  \"category\": \"Food\",\n"
            "  \"price\": \"20000 VND\",\n"
            "  \"description\": \"Fast delivery for expats\"\n"
            "}\n"
            "```\n"
            "Or just tell me the *name* to begin the guided flow."
        )
        return {
            "handled": True,
            "reply": reply,
            "meta": {"agent_id": agent_id, "intent": "add_service"}
        }

    # -------------------------
    # 3) FALLBACK — LLM service agent (unchanged)
    # -------------------------
    try:
        import asyncio
        from app.agents import service_agent as SA

        loop = asyncio.get_event_loop()
        handled, answer = loop.run_until_complete(
            SA.handle_message(user_id=user_id, text=t, channel="http")
        )
        return {
            "handled": bool(handled),
            "reply": answer or "",
            "meta": {"agent_id": agent_id, "mode": "llm"},
        }

    except RuntimeError:
        # No running loop – create one
        import asyncio
        from app.agents import service_agent as SA

        loop = asyncio.new_event_loop()
        try:
            handled, answer = loop.run_until_complete(
                SA.handle_message(user_id=user_id, text=t, channel="http")
            )
        finally:
            loop.close()
        return {
            "handled": bool(handled),
            "reply": answer or "",
            "meta": {"agent_id": agent_id, "mode": "llm"},
        }

    except Exception as e:
        # Safe stub so HTTP never explodes
        return {
            "handled": True,
            "reply": f"[stub] {t}",
            "meta": {"agent_id": agent_id, "error": str(e)},
        }
