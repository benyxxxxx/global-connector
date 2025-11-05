from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

class ServiceIn(BaseModel):
    business_name: str = Field(min_length=1)
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = ""
    category: Optional[str] = None
    category_name: Optional[str] = None
    pricing_model: Optional[str] = None
    currency: Optional[str] = "VND"
    base_price: Optional[float] = None
    location: Optional[str] = None
    place: Optional[str] = None
    delivery: Optional[bool] = None
    requires_booking: Optional[bool] = None
    time_unit: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None

    @validator("pricing_model", always=True)
    def resolve_pricing_model(cls, v, values):
        if v is None:
            base_price = values.get("base_price")
            return "flat" if base_price is not None else "time_based"
        return v

    @property
    def resolved_name(self) -> str:
        return self.name or self.title or ""

    @property
    def resolved_category(self) -> str:
        return self.category or self.category_name or ""

class ImportPayload(BaseModel):
    items: List[ServiceIn]
