# app/models/memory.py
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


class Memory(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: str = Field(index=True)
    reference: str = Field(index=True)
    memory: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
