
from __future__ import annotations
from typing import Tuple, Dict, Any, List
import os
from dateutil import parser as dateparser
try:
    from app.deps import GLOBAL_PROMO_CODE  # if your project defines it
except Exception:
    GLOBAL_PROMO_CODE = os.getenv("GLOBAL_PROMO_CODE", "")
from app.agents.intent import detect_intent
from app.clients import backend_api as be

STATE: Dict[str, Dict[str, Any]] = {}

def _st(u: str) -> Dict[str, Any]:
    return STATE.setdefault(u, {"stage": "idle", "ctx": {}})

# entrypoints for DAO-launched services
async def start_food(user_id: str, defaults=None) -> Tuple[bool, str]:
    st = _st(user_id); st["stage"] = "food:list"; st["ctx"] = {}
    services = await be.list_services(user_id=user_id)
    menu = [s for s in services if (s.get("flow_key") == "food" or "food" in (s.get("tags") or []))]
    st["ctx"]["menu"] = menu
    return True, _render_menu(menu)

async def start_real_estate(user_id: str, defaults=None) -> Tuple[bool, str]:
    st = _st(user_id); st["stage"] = "re:start"; st["ctx"] = {}
    return True, _re_prompt()

def _render_menu(menu: List[Dict[str, Any]]) -> str:
    if not menu:
        return "No food items published yet."
    lines = ["Here are some options:\n"]
    for i, s in enumerate(menu, 1):
        name = s.get("name", f"Item {i}")
        price = s.get("price")
        currency = s.get("currency") or "USD"
        price_str = f"${price:.2f} {currency}" if isinstance(price, (int, float)) else "-"
        lines.append(f"{i}. {name} — {price_str}")
    lines.append("\nReply with the number to select.")
    return "\n".join(lines)

async def handle_message(user_id: str, text: str, channel: str = "http") -> Tuple[bool, str]:
    st = _st(user_id)
    stage = st.get("stage", "idle")
    t = (text or "").strip()

    # continue flow if already inside
    if stage.startswith("food:"):
        return await _food_flow(user_id, t, channel, st)
    if stage.startswith("re:"):
        return await _real_estate_flow(user_id, t, channel, st)

    # detect intent
    intent = detect_intent(t)
    if intent == "food":
        return await start_food(user_id)
    elif intent == "real_estate":
        return await start_real_estate(user_id)
    else:
        return False, "I can help with food orders or real-estate inquiries. Try: \"I want food\" or \"I want to rent a flat\"."

async def _food_flow(user_id: str, t: str, channel: str, st: Dict[str, Any]) -> Tuple[bool, str]:
    stage = st["stage"]; ctx = st["ctx"]

    if stage == "food:list":
        menu = ctx.get("menu") or []
        if not menu:
            services = await be.list_services(user_id=user_id)
            menu = [s for s in services if (s.get("flow_key") == "food" or "food" in (s.get("tags") or []))]
            ctx["menu"] = menu
        try:
            idx = int(t)
        except:
            return True, "Please send the number of the item you want."
        if idx < 1 or idx > len(menu):
            return True, "Please pick a valid number from the list."
        item = menu[idx-1]
        ctx["item"] = item
        st["stage"] = "food:mode"
        return True, "Would you like to *Visit Restaurant* or *Get Delivery*?"

    if stage == "food:mode":
        lt = t.lower()
        if "visit" in lt:
            item = ctx.get("item", {})
            try:
                await be.create_booking(user_id, {
                    "service_id": item.get("id"),
                    "service_name": item.get("name"),
                    "requested_time": None,
                    "channel": channel,
                    "price": item.get("price"),
                    "currency": item.get("currency") or "USD",
                    "attributes": {"flow":"food","mode":"visit","source":"router"},
                })
            except Exception:
                pass
            STATE.pop(user_id, None)
            return True, f"Great — visit confirmed for {item.get('name')}. Enjoy!"
        if "delivery" in lt:
            st["stage"] = "food:time"
            return True, "Delivery — got it. Do you want it *Now* or *Later*?"
        return True, "Please reply with *Visit Restaurant* or *Get Delivery*."

    if stage == "food:time":
        lt = t.lower()
        if lt in ("now", "right now", "asap"):
            requested_time = None
        else:
            try:
                requested_time = dateparser.parse(t, fuzzy=True).isoformat()
            except:
                return True, "I couldn't parse that time. Try 'now' or 'today 7pm'."

        item = ctx.get("item", {})
        try:
            await be.create_booking(user_id, {
                "service_id": item.get("id"),
                "service_name": item.get("name"),
                "requested_time": requested_time,
                "channel": channel,
                "price": item.get("price"),
                "currency": item.get("currency") or "USD",
                "attributes": {"flow":"food","mode":"delivery","source":"router"},
            })
        except Exception:
            pass
        STATE.pop(user_id, None)
        promo = f" Use promo code **{GLOBAL_PROMO_CODE}**!" if GLOBAL_PROMO_CODE else ""
        ts = "ASAP" if requested_time is None else requested_time.replace("T"," ")[:16]
        return True, f"✅ Booking created for *{item.get('name')}* at {ts}.{promo}"

    return True, "Let's start over. Say 'I want food'."

def _re_prompt() -> str:
    return "Are you looking for a *short-term* stay (days/weeks) or a *long-term* lease (months/years)?"

async def _real_estate_flow(user_id: str, t: str, channel: str, st: Dict[str, Any]) -> Tuple[bool, str]:
    lt = t.lower()
    if st["stage"] == "re:start":
        if "short" in lt:
            STATE.pop(user_id, None)
            return True, "Short-term noted. I’ll fetch listings next."
        if any(k in lt for k in ("long","months","years","rent","lease")):
            STATE.pop(user_id, None)
            return True, "Long-term lease noted. I’ll fetch listings next."
        return True, "Please reply with *short-term* or *long-term*."
    return True, "Let's start over. Say 'I want to rent a flat'."
