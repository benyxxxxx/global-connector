from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.schemas.service_in import ServiceIn, ImportPayload
from app.clients import backend_api as be

router = APIRouter(prefix="", tags=["services-import"])

@router.post("/services/import-json")
async def import_services(payload: ImportPayload):
    out = []
    for item in payload.items:
        name = item.resolved_name
        if not name:
            raise HTTPException(status_code=422, detail="missing name or title")
        category = item.resolved_category
        if not category:
            raise HTTPException(status_code=422, detail="missing category")

        created = await be.create_service(
            user_id="system",
            business_name=item.business_name,
            name=name,
            description=item.description or "",
            category_name=category,
            pricing_model=item.pricing_model,
            currency=item.currency or "VND",
            base_price=float(item.base_price) if item.base_price is not None else 0.0,
            location=item.location,
            place=item.place,
            delivery=item.delivery,
            requires_booking=item.requires_booking,
            time_unit=item.time_unit,
            min_duration=item.min_duration,
            max_duration=item.max_duration,
            attributes=item.attributes,
        )
        out.append(created or {"name": name})
    return {"ok": True, "count": len(out)}
