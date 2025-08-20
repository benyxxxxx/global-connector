from __future__ import annotations

import os
import json
import inspect
import logging
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path

from app.llm import LLMClient
from app.clients import backend_api as be

logger = logging.getLogger(__name__)

USE_INTENT_ENGINE = os.getenv("USE_INTENT_ENGINE", "true").lower() == "true"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "orchestrator_prompt.txt"

try:
    SYS_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
except Exception:
    SYS_PROMPT = "You are the orchestrator agent. Use tools when helpful and keep answers short."

CHAT_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browse_services",
            "description": "Search or list public services for the user.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "Return available service categories.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Books a service for a user. Requires service_id, user's full_name, and a scheduled_at time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                    "full_name": {"type": "string"},
                    "scheduled_at": {"type": "string", "format": "date-time"},
                    "duration": {"type": "integer"},
                },
                "required": ["service_id", "full_name", "scheduled_at"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_service",
            "description": "Fetch a single service by ID to determine which booking fields are required (e.g., duration for time-based, address for delivery, variant choice, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                },
                "required": ["service_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": "Create a booking once all required info is gathered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string"},
                    "full_name": {"type": "string"},
                    "scheduled_at": {"type": "string", "format": "date-time"},
                    "duration": {"type": "integer"},
                    "attributes": { "type": "object", "additionalProperties": True },
                },
                "required": ["service_id", "full_name", "scheduled_at"],
            },
        },
    },
]

AVAILABLE_TOOLS = {
    "browse_services": be.list_services,
    "list_categories": be.list_categories,
    "create_booking": be.create_booking,
    "create_booking": be.create_booking,
}


def _safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=repr)
    except Exception:
        return json.dumps(str(obj), ensure_ascii=False)


def _get_tool_call_id(tc: Any) -> str:
    if hasattr(tc, "id"):
        return getattr(tc, "id", "") or ""
    if hasattr(tc, "model_dump"):
        return (tc.model_dump() or {}).get("id", "") or ""
    if isinstance(tc, dict):
        return tc.get("id", "") or ""
    return ""


def _extract_tool_call_components(tc: Any) -> Tuple[Optional[str], Optional[str], str]:
    """
    Returns (id, name, args_json_str) for various SDK shapes.
    """
    try:
        # SDK object
        if hasattr(tc, "function"):
            fn = tc.function
            return _get_tool_call_id(tc), getattr(fn, "name", None), (getattr(fn, "arguments", "") or "{}")

        # Pydantic-like
        if hasattr(tc, "model_dump"):
            d = tc.model_dump() or {}
            fn = d.get("function") or {}
            return d.get("id", ""), fn.get("name"), (fn.get("arguments") or "{}")

        # Dict
        if isinstance(tc, dict):
            fn = tc.get("function") or {}
            return tc.get("id", ""), fn.get("name"), (fn.get("arguments") or "{}")
    except Exception:
        pass
    return None, None, "{}"


def _extract_tool_call(tc: Any) -> Tuple[Optional[str], Dict]:
    """
    Returns (name, args_dict) for execution.
    """
    _, name, args_raw = _extract_tool_call_components(tc)
    try:
        args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
    except Exception:
        args = {}
    return name, args


async def _maybe_decide_intent(text: str, lang_hint: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        from app.intent.engine import decide_intent
    except Exception as e:
        logger.warning("Intent engine import failed: %s", e)
        return None

    try:
        if inspect.iscoroutinefunction(decide_intent):
            return await decide_intent(text, lang_hint)
        res = decide_intent(text, lang_hint)
        if inspect.isawaitable(res):
            res = await res
        return res
    except Exception as e:
        logger.exception("decide_intent failed: %s", e)
        return None


async def _run_tool(fn: Any, user_id: str, payload: Dict[str, Any]) -> Any:
    try:
        if inspect.iscoroutinefunction(fn):
            try:
                return await fn(user_id=user_id, **(payload or {}))
            except TypeError:
                return await fn(user_id, **(payload or {}))
        else:
            res = None
            try:
                res = fn(user_id=user_id, **(payload or {}))
            except TypeError:
                res = fn(user_id, **(payload or {}))
            if inspect.isawaitable(res):
                res = await res
            return res
    except Exception as e:
        logger.exception("Tool execution failed (%s): %s", getattr(fn, "__name__", "tool"), e)
        return {"error": str(e)}


async def handle_message(user_id: str, text: str, channel: str = "http") -> Tuple[bool, str]:
    """
    System prompt -> (optional intent hint) -> user -> LLM -> tools -> final LLM.
    """
    messages = CHAT_HISTORY.setdefault(user_id, [])

    # Ensure system prompt at the start of the conversation
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": SYS_PROMPT})

    # Intent hint
    if USE_INTENT_ENGINE:
        hint = await _maybe_decide_intent(text, None)
        if hint:
            messages.append({"role": "system", "content": f"[intent_hint]{_safe_json_dumps(hint)}"})

    # User turn
    messages.append({"role": "user", "content": text})

    llm = LLMClient()

    # 1st pass — may contain tool calls
    reply = await llm.get_agent_response(messages, TOOLS)

    # Extract tool calls from reply (supports different SDK shapes)
    tool_calls = getattr(reply, "tool_calls", None) or (getattr(reply, "additional_kwargs", {}) or {}).get("tool_calls")

    if tool_calls:
        # IMPORTANT: append the assistant message that CONTAINS tool_calls
        # so that 'tool' messages have a valid preceding assistant turn.
        assistant_tc_list: List[Dict[str, Any]] = []
        for tc in tool_calls:
            tc_id, tc_name, tc_args_raw = _extract_tool_call_components(tc)
            if not tc_name:
                continue
            assistant_tc_list.append(
                {
                    "id": tc_id or "",
                    "type": "function",
                    "function": {"name": tc_name, "arguments": tc_args_raw or "{}"},
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": getattr(reply, "content", None) or "",
                "tool_calls": assistant_tc_list,
            }
        )

        # Execute tools and append 'tool' messages right after (no other roles in between)
        for tc in tool_calls:
            tc_id, tc_name, _tc_args_raw = _extract_tool_call_components(tc)
            name, payload = _extract_tool_call(tc)
            if not name:
                continue

            fn = AVAILABLE_TOOLS.get(name)
            if not fn:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id or "",
                        "content": _safe_json_dumps({"error": f"unknown tool: {name}"}),
                    }
                )
                continue

            result = await _run_tool(fn, user_id=user_id, payload=payload or {})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc_id or "",
                    "content": _safe_json_dumps(result),
                }
            )

        # 2nd pass — produce final user-facing answer
        reply = await llm.get_agent_response(messages, TOOLS)

    final_text = getattr(reply, "content", None) or str(reply)
    messages.append({"role": "assistant", "content": final_text})

    return True, final_text
