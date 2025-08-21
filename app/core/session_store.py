from __future__ import annotations
import os, json, threading
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(os.getenv("ROUTER_DATA_DIR", "/mnt/data/router_data")).resolve()
_SESS_PATH = _DATA_DIR / "chat_sessions.json"
_LOCK = threading.Lock()

def _load() -> dict:
    if not _SESS_PATH.exists():
        return {}
    try:
        with _SESS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(d: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _SESS_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    tmp.replace(_SESS_PATH)

def set_active(chat_id: str, agent_id: str) -> None:
    with _LOCK:
        d = _load()
        d[chat_id] = agent_id
        _save(d)

def get_active(chat_id: str) -> Optional[str]:
    with _LOCK:
        d = _load()
        return d.get(chat_id)

def clear_active(chat_id: str) -> None:
    with _LOCK:
        d = _load()
        if chat_id in d:
            del d[chat_id]
            _save(d)
