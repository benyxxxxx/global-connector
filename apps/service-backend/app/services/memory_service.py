from sqlmodel import Session, select
from datetime import datetime
from typing import Optional
from app.models.memory import Memory


class MemoryService:
    def __init__(self, session: Session):
        self.session = session

    def get_memory(
        self,
        key: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Memory]:
        query = select(Memory)
        if key:
            query = query.where(Memory.key == key)
        if user_id:
            query = query.where(Memory.user_id == user_id)
        if agent_id:
            query = query.where(Memory.agent_id == agent_id)

        return self.session.exec(query).first()

    def save_memory(
        self,
        memory_text: str,
        key: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Memory:
        existing = self.get_memory(key=key, user_id=user_id, agent_id=agent_id)
        now = datetime.utcnow()

        if existing:
            existing.memory = memory_text
            existing.updated_at = now
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        new_memory = Memory(
            key=key,
            user_id=user_id,
            agent_id=agent_id,
            memory=memory_text,
            updated_at=now,
        )
        self.session.add(new_memory)
        self.session.commit()
        self.session.refresh(new_memory)
        return new_memory
