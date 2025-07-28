from pydantic import EmailStr, field_validator
from sqlmodel import SQLModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.business import BusinessType


class BusinessBase(SQLModel):
    owner_id: str
    name: str
    description: Optional[str] = None
    type: BusinessType
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BusinessCreate(SQLModel):
    name: str
    description: Optional[str] = None
    type: BusinessType
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Business name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("Business name must be at least 2 characters long")
        return v.strip()

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) < 10:
            raise ValueError("Contact phone must be at least 10 characters long")
        return v.strip() if v else None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v.strip() if v else None


class BusinessUpdate(SQLModel):
    owner_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[BusinessType] = None
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Business name cannot be empty")
            if len(v.strip()) < 2:
                raise ValueError("Business name must be at least 2 characters long")
            return v.strip()
        return v

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) < 10:
            raise ValueError("Contact phone must be at least 10 characters long")
        return v.strip() if v else None

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v.strip() if v else None


class BusinessResponse(SQLModel):
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    type: BusinessType
    address: Optional[str]
    contact_email: Optional[EmailStr]
    contact_phone: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class BusinessFilter(SQLModel):
    owner_id: Optional[str] = None
    type: Optional[BusinessType] = None
    name: Optional[str] = None  # For name search
    location: Optional[str] = None  # For address search


class BusinessSummary(SQLModel):
    """Lightweight business info for listings"""

    id: str
    name: str
    type: BusinessType
    address: Optional[str]
    contact_email: Optional[EmailStr]
