from __future__ import annotations
from typing import Optional, Dict, Any
from app import crud
from app.db import SessionLocal

def get_session(chat_id: str) -> Dict[str, Any]:
    """Gets the full session data for a chat from the database."""
    db = SessionLocal()
    session = crud.get_session(db, chat_id)
    db.close()
    if session:
        return session.data
    return {}

def update_session(chat_id: str, data: Dict[str, Any]) -> None:
    """Updates the session data for a chat in the database."""
    db = SessionLocal()
    crud.update_session(db, chat_id, data)
    db.close()

def clear_session_state(chat_id: str) -> None:
    """Clears the conversational state, but keeps the active agent."""
    db = SessionLocal()
    session = crud.get_session(db, chat_id)
    if session:
        active_agent = session.data.get("active_agent")
        new_data = {}
        if active_agent:
            new_data["active_agent"] = active_agent
        crud.update_session(db, chat_id, new_data)
    db.close()


def set_active(chat_id: str, agent_id: str) -> None:
    """Sets the active agent for a chat."""
    update_session(chat_id, {"active_agent": agent_id})


def get_active(chat_id: str) -> Optional[str]:
    """Gets the active agent for a chat."""
    return get_session(chat_id).get("active_agent")


def clear_active(chat_id: str) -> None:
    """Clears the active agent for a chat."""
    db = SessionLocal()
    session = crud.get_session(db, chat_id)
    if session and "active_agent" in session.data:
        new_data = session.data.copy()
        del new_data["active_agent"]
        crud.update_session(db, chat_id, new_data)
    db.close()