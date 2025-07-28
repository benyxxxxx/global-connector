# app/schemas/memory.py
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class MemoryCreateUpdate(BaseModel):
    reference: str
    memory: str

class MemoryRead(BaseModel):
    id: UUID
    reference: str
    memory: str
    updated_at: datetime

    class Config:
        orm_mode = True
