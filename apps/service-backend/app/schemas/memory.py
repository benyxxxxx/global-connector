from pydantic import BaseModel, constr
from typing import Optional
from uuid import UUID


class AgentMemoryCreate(BaseModel):
    user_id: Optional[str]
    agent_id: Optional[str]
    memory: constr(min_length=1)
    memory_type: Optional[str] = "user"


class AgentMemoryRead(BaseModel):
    id: UUID
    user_id: Optional[str]
    agent_id: Optional[str]
    memory: str
    memory_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
