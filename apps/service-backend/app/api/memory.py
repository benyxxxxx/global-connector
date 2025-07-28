from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, create_engine, SQLModel
from app.schemas.memory import AgentMemoryCreate, AgentMemoryRead
from typing import Optional
from app.api.deps import get_booking_service


@app.get("/memory", response_model=AgentMemoryRead)
def read_memory(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    session: Session = Depends(get_session),
):
    service = AgentMemoryService(session)
    memory = service.get_memory(user_id=user_id, agent_id=agent_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@app.post("/memory", response_model=AgentMemoryRead)
def save_memory(
    memory_in: AgentMemoryCreate, session: Session = Depends(get_session)
):
    service = AgentMemoryService(session)
    memory = service.save_memory(
        user_id=memory_in.user_id,
        agent_id=memory_in.agent_id,
        memory=memory_in.memory,
        memory_type=memory_in.memory_type,
    )
    return memory
