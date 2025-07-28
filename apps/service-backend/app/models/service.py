from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from decimal import Decimal
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
    JSON,
    Column,
    Enum as SqlEnum,
    DECIMAL,
)
from pydantic import BaseModel, ConfigDict, model_validator


# Enums
class PricingType(str, Enum):
    FLAT = "flat"
    TIME_BASED = "time_based"


class TimeUnit(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class VariantType(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


# Pydantic Models for JSON fields
class PricingTier(BaseModel):
    duration: int
    price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)

    # @model_validator(mode="after")
    # def validate_time_unit_required(self) -> 'Pricing':
    #     if self.type == PricingType.TIME_BASED and self.time_unit is None:
    #         raise ValueError("time_unit is required when pricing type is 'time_based'")
    #     return self


class VariantOption(BaseModel):
    name: str
    price_change: Optional[Decimal] = Field(
        default=None, decimal_places=2, max_digits=10
    )
    available: bool = True


class Variant(BaseModel):
    name: str
    type: VariantType = VariantType.SINGLE
    required: bool
    options: List[VariantOption]


# SQLModel Tables
class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: str = Field(primary_key=True)

    name: str = Field(index=True)
    description: Optional[str] = None
    # business_id: str = Field(foreign_key="businesses.id", index=True)
    owner_id: str = Field(index=True)

    pricing_model: Optional[str] = Field(default="")
    currency: Optional[str] = Field(default="")
    base_price: Optional[Decimal] = Field(
        default=None, sa_column=Column(DECIMAL(10, 2))
    )

    time_unit: Optional[str] = Field(default=None)

    min_duration: Optional[int] = Field(default=None)
    max_duration: Optional[int] = Field(default=None)

    pricing_tiers: Optional[List[PricingTier]] = Field(
        default=None, sa_column=Column(JSON)
    )
    variants: Optional[List[Variant]] = Field(default=None, sa_column=Column(JSON))

    # JSON field for flexible
    attributes: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    bookings: List["Booking"] = Relationship(back_populates="service")
    # business: Optional["Business"] = Relationship(back_populates="services")
