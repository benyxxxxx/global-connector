from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class MemoryCreateUpdate(BaseModel):
    key: Optional[str]
    user_id: Optional[str]
    agent_id: Optional[str]
    memory: str


class MemoryRead(BaseModel):
    id: UUID
    key: Optional[str]
    user_id: Optional[str]
    agent_id: Optional[str]
    memory: str
    updated_at: datetime

    class Config:
        orm_mode = True
