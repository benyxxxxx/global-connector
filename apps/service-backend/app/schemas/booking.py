# app/schemas/booking.py
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from .service import ServiceResponse
from app.models.booking import BookingStatus


class BookingBase(BaseModel):
    service_id: str
    user_id: str
    # variant_id: Optional[str] = None
    service_snapshot: Dict[str, Any]
    scheduled_at: datetime
    total_price: Optional[Decimal]
    base_price: Optional[Decimal]
    duration: Optional[int]
    status: BookingStatus = BookingStatus.PENDING
    attributes: Optional[Dict[str, Any]] = None


class BookingCreate(BaseModel):
    service_id: str
    # variant_id: Optional[str] = None
    scheduled_at: datetime
    duration: Optional[int]
    attributes: Optional[Dict[str, Any]] = None
    force_add: Optional[bool] = None


class BookingCreateValidated(BookingCreate):
    total_price: Optional[Decimal]
    base_price: Optional[Decimal]

class BookingUpdate(BaseModel):
    # status: Optional[BookingStatus] = None
    attributes: Optional[Dict[str, Any]] = None
    duration: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class BookingResponse(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
