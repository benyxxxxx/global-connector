from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
from app.utils.ids import generate_unique_id
from sqlmodel import SQLModel, Field, Column, JSON, Relationship, DECIMAL


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CARD = "card"
    MANDEL_COIN = "mandel_coin"


class PaymentProvider(str, Enum):
    SOLANA = "solana"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: str = Field(
        default_factory=lambda: generate_unique_id(), primary_key=True, index=True
    )
    user_id: Optional[str] = Field(default=None)
    booking_id: Optional[str] = Field(default=None, foreign_key="bookings.id", index=True)

    reference_type: Optional[str] = Field(default=None, index=True)  
    reference_id: Optional[str] = Field(default=None, index=True)    

    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)

    amount: Decimal = Field(
        decimal_places=2, max_digits=10, sa_column=Column(DECIMAL(10, 2))
    )
    currency: str = Field(default="USD")

    payment_method: PaymentMethod = Field(default=PaymentMethod.CARD)

    external_id: Optional[str] = Field(
        default=None, index=True
    )  # Stripe payment_intent_id, etc.
    transaction_id: Optional[str] = Field(
        default=None, index=True
    )  # Final transaction ID
    provider: str = Field(default="")

    paid_at: Optional[datetime] = None
    payment_metadata: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    booking: Optional["Booking"] = Relationship(back_populates="payments")
