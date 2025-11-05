from __future__ import annotations
from typing import Any, Dict, List
import json
import re
from app.schemas.service_in import ServiceIn
from app.clients import backend_api as be

# Matches:
#   /addservicefile:{ JSON }
#   /addservicefile { JSON }
#   /addservicefile\n[ JSON_ARRAY ]
CMD_RE = re.compile(r"^\s*/addservicefile\s*[:\n\s]+(\{.*|\[.*)$", re.IGNORECASE | re.DOTALL)

def _coerce_items(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                raise ValueError("array items must be objects")
        return data
    raise ValueError("json must be an object or an array")

async def add_from_text(text: str, chat_id: str, user_id: str):
    m = CMD_RE.match(text or "")
    if not m:
        return {"ok": False, "error": "no_command_match"}
    raw = m.group(1).strip()
    try:
        data = json.loads(raw)
    except Exception as e:
        return {"ok": False, "error": f"invalid_json: {e}"}

    items = _coerce_items(data)

    validated: List[ServiceIn] = []
    for obj in items:
        # map aliases title->name before validation convenience
        obj = dict(obj)
        if "name" not in obj and "title" in obj:
            obj["name"] = obj.get("title")
        if "category_name" not in obj and "category" in obj:
            obj["category_name"] = obj.get("category")
        item = ServiceIn(**obj)
        if not item.resolved_name:
            return {"ok": False, "error": "missing name or title"}
        if not item.resolved_category:
            return {"ok": False, "error": "missing category"}
        validated.append(item)

    created_count = 0
    titles: List[str] = []
    for it in validated:
        name = it.resolved_name
        res = await be.create_service(
            user_id=user_id,
            business_name=it.business_name,
            name=name,
            description=it.description or "",
            category_name=it.resolved_category,
            pricing_model=it.pricing_model,
            currency=it.currency or "VND",
            base_price=float(it.base_price) if it.base_price is not None else 0.0,
            location=it.location,
            place=it.place,
            delivery=it.delivery,
            requires_booking=it.requires_booking,
            time_unit=it.time_unit,
            min_duration=it.min_duration,
            max_duration=it.max_duration,
            attributes=it.attributes,
        )
        titles.append(name)
        created_count += 1

    return {"ok": True, "count": created_count, "titles": titles}
