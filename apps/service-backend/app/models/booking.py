from enum import Enum
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON, Relationship


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: str = Field(primary_key=True, index=True)
    service_id: str = Field(index=True, foreign_key="services.id")
    user_id: str = Field(index=True)

    variant_id: Optional[str] = Field(default=None, index=True)
    status: BookingStatus = Field(default=BookingStatus.PENDING)

    # JSON fields
    service_snapshot: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False), default_factory=dict
    )
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    scheduled_at: datetime
    duration: Optional[int] = Field(default=None)

    base_price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10)
    total_price: Optional[Decimal] = Field(
        default=None, decimal_places=2, max_digits=10
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 👇 Relationship to Service
    service: Optional["Service"] = Relationship(back_populates="bookings")
    payments: List["Payment"] = Relationship(back_populates="booking")
