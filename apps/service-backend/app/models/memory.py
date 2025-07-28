from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class Memory(SQLModel, table=True):
    __tablename__ = "memories"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: Optional[str] = Field(default=None, index=True)  # e.g. "user_preferences", "session_123_memory"
    user_id: Optional[str] = Field(default=None, index=True)
    agent_id: Optional[str] = Field(default=None, index=True)
    memory: str  # text blob
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
