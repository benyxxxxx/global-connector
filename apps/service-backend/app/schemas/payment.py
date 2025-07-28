from pydantic import BaseModel as PydanticBaseModel, model_validator
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal
from datetime import datetime
from app.models.payment import PaymentStatus, PaymentMethod, PaymentProvider


# -----------------------------
# Shared base schema
# -----------------------------
class PaymentBase(PydanticBaseModel):
    id: str
    user_id: Optional[str]
    reference_type: Optional[str] 
    reference_id: Optional[str] 
    booking_id: Optional[str]
    status: PaymentStatus = PaymentStatus.PENDING
    amount: Decimal
    currency: str = "USD"
    payment_method: PaymentMethod = PaymentMethod.CARD
    external_id: Optional[str] = None
    transaction_id: Optional[str] = None
    provider: PaymentProvider = ""
    paid_at: Optional[datetime] = None
    payment_metadata: Dict[str, Any] = {}

    # class Config:
    #     orm_mode = True


# -----------------------------
# Create schema
# -----------------------------
class PaymentRequest(PydanticBaseModel):
    booking_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    amount: Decimal = None
    payment_method: PaymentMethod
    # force_add: Optional[bool] = False

    @model_validator(mode="after")
    def validate_reference_or_booking(self) -> "PaymentRequest":
        if not self.booking_id and not self.reference_id:
            raise ValueError("Either 'booking_id' or 'reference_id' must be provided.")

        if self.reference_id and not self.amount:
            raise ValueError("'amount' is required when 'reference_id' is provided.")


        return self


class PaymentCreate(PydanticBaseModel):
    status: PaymentStatus = PaymentStatus.PENDING
    reference_type: Optional[str] = None
    reference_id: Optional[str]  = None
    amount: Decimal
    currency: str = "USD"
    payment_method: PaymentMethod = PaymentMethod.CARD
    external_id: Optional[str] = None
    transaction_id: Optional[str] = None
    provider: PaymentProvider = ""
    payment_metadata: Dict[str, Any] = {}


# -----------------------------
# Update schema
# -----------------------------
class PaymentUpdate(PydanticBaseModel):
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    external_id: Optional[str] = None
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


# -----------------------------
# Read schema (e.g. for GET response)
# -----------------------------
class PaymentResponse(PaymentBase):
    id: str
    created_at: datetime
    updated_at: datetime
