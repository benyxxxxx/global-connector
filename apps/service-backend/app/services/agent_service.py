from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime
from app.models.memory import AgentMemory


class AgentMemoryService:
    def __init__(self, session: Session):
        self.session = session

    def get_memory(
        self, user_id: Optional[str] = None, agent_id: Optional[str] = None
    ) -> Optional[AgentMemory]:
        query = select(AgentMemory)
        if user_id and agent_id:
            query = query.where(
                (AgentMemory.user_id == user_id) & (AgentMemory.agent_id == agent_id)
            )
        elif user_id:
            query = query.where(AgentMemory.user_id == user_id)
        elif agent_id:
            query = query.where(AgentMemory.agent_id == agent_id)
        else:
            return None

        return self.session.exec(query).first()

    def save_memory(
        self,
        user_id: Optional[str],
        agent_id: Optional[str],
        memory: str,
        memory_type: str = "user",
    ) -> AgentMemory:
        existing = self.get_memory(user_id, agent_id)

        now = datetime.utcnow()
        if existing:
            existing.memory = memory
            existing.memory_type = memory_type
            existing.updated_at = now
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        new_memory = AgentMemory(
            user_id=user_id,
            agent_id=agent_id,
            memory=memory,
            memory_type=memory_type,
            created_at=now,
            updated_at=now,
        )
        self.session.add(new_memory)
        self.session.commit()
        self.session.refresh(new_memory)
        return new_memory
