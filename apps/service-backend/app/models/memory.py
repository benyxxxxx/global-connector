from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class AgentMemory(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    agent_id: Optional[str] = Field(default=None, index=True)
    memory: str
    memory_type: str = Field(default="user", index=True)  # 'user', 'agent', or 'user-agent'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
