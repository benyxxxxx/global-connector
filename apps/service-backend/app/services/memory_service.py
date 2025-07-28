# app/services/memory_service.py
from sqlmodel import Session, select
from app.models.memory import Memory
from typing import Optional


class MemoryService:
    def __init__(self, session: Session):
        self.session = session

    def get_memory(self, reference: str, user_id: str) -> Optional[Memory]:
        statement = select(Memory).where(Memory.reference == reference, Memory.user_id == user_id)
        result = self.session.exec(statement).first()
        return result

    def save_memory(self, reference: str, memory_text: str, user_id: str) -> Memory:
        # Try to find existing memory
        existing = self.get_memory(reference=reference, user_id=user_id)
        if existing:
            existing.memory = memory_text
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing

        new_memory = Memory(reference=reference, memory=memory_text, user_id=user_id)
        self.session.add(new_memory)
        self.session.commit()
        self.session.refresh(new_memory)
        return new_memory
