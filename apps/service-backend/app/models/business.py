from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from datetime import timezone
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import EmailStr


class BusinessType(str, Enum):
    RESTAURANT = "restaurant"
    HOSTEL = "hostel"
    RENTAL = "rental"
    TOUR = "tour"
    SHOP = "shop"
    GYM = "gym"
    ACTIVITY = "activity"
    SPA = "spa"
    OTHER = "other"


class Business(SQLModel, table=True):

    __tablename__ = "businesses"

    id: str = Field(primary_key=True)
    owner_id: str = Field(index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    type: BusinessType = Field(index=True)
    address: Optional[str] = Field(default=None)
    contact_email: Optional[EmailStr] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # services: List["Service"] = Relationship(back_populates="business")
