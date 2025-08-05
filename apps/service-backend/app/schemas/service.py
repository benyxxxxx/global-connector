from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.service import Variant, PricingTier, PricingType, TimeUnit


class ServiceBase(BaseModel):
    business_name: Optional[str]
    name: str
    description: Optional[str] = None
    # business_id: str

    pricing_model: PricingType
    currency: str = "USD"
    base_price: Decimal

    time_unit: Optional[TimeUnit] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    
    location: Optional[str] = None
    place: Optional[bool] = False
    delivery: Optional[bool] = False
    requires_booking: Optional[bool] = False

    # pricing_tiers: Optional[List[PricingTier]] = None
    # variants: Optional[List[Variant]] = None

    attributes: Optional[Dict[str, Any]] = None


# Request/Response Models
class ServiceCreate(BaseModel):
    business_name: str
    name: str
    description: Optional[str] = None
    # business_id: str

    pricing_model: PricingType
    currency: str
    base_price: Decimal

    time_unit: Optional[TimeUnit] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None

    location: Optional[str] = None
    place: Optional[bool] = False
    delivery: Optional[bool] = False
    requires_booking: Optional[bool] = False
    
    # pricing_tiers: Optional[List[PricingTier]] = None
    # variants: Optional[List[Variant]] = None

    attributes: Optional[Dict[str, Any]] = None


class ServiceUpdate(BaseModel):
    business_name: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    pricing_model: Optional[PricingType] = None
    currency: Optional[str] = None
    base_price: Optional[Decimal] = None

    time_unit: Optional[TimeUnit] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    
    location: Optional[str] = None
    place: Optional[bool] = None
    delivery: Optional[bool] = None
    requires_booking: Optional[bool] = None

    pricing_tiers: Optional[List[PricingTier]] = None
    # variants: Optional[List[Variant]] = None
    # attributes: Optional[Dict[str, Any]] = None


class ServiceResponse(ServiceBase):
    # model_config = ConfigDict(from_attributes=True)
    id: str
    owner_id: str
    # business_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 