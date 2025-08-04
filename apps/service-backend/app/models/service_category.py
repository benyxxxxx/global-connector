# In app/models/service_category.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class ServiceCategory(SQLModel, table=True):
    __tablename__ = "service_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None

    services: List["Service"] = Relationship(back_populates="service_category")