from pydantic import BaseModel, Field
from typing import Optional

class ServiceCategoryBase(BaseModel):
    name: str = Field(..., example="tech")
    description: Optional[str] = Field(None, example="Phone and computer repair services")

class ServiceCategoryCreate(ServiceCategoryBase):
    pass

class ServiceCategoryResponse(ServiceCategoryBase):
    id: int = Field(..., example=7)

    class Config:
        from_attributes = True