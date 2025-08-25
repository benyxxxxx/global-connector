import os
from typing import Optional

# ⬇️ import your existing bits
# from app.orchestrator.runtime import run_orchestrator  # <- your function that talks to LLM + tools
# from app.db import SessionLocal
# from app.models import Agent, Session, AgentMemory  # rename to your actual models

DEFAULT_AGENT_ID = os.getenv("DEFAULT_AGENT_ID", "agent_service")

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
    agent_id = agent_id or DEFAULT_AGENT_ID
    # r = run_orchestrator(chat_id=chat_id, user_id=user_id, text=text, agent_id=agent_id)
    # add_memory(db, agent_id, chat_id, "user", text); add_memory(db, agent_id, chat_id, "assistant", r.reply)
    # return {"handled": True, "reply": r.reply, "meta": r.meta}
    return {"handled": True, "reply": f"[stub] {text}", "meta": {"agent_id": agent_id}}
