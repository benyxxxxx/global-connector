from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import Optional

from app.database import get_session
from app.services.memory_service import MemoryService
from app.schemas.memory import MemoryRead, MemoryCreateUpdate
from app.security import get_current_user_id
from .deps import get_memory_service

router = APIRouter()


@router.get("/", response_model=MemoryRead)
def read_memory(
    key: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    agent_id: Optional[str] = Query(default=None),
    memory_service: MemoryService = Depends(get_memory_service),
    current_user_id: str = Depends(get_current_user_id),
):
    memory = memory_service.get_memory(key=key, user_id=user_id, agent_id=agent_id)

    if(user_id!=current_user_id):
        raise HTTPException(status_code=401, detail="Unable to get memory, user must be same")

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.post(
    "/",
    response_model=MemoryRead,
    status_code=status.HTTP_201_CREATED,
)
def save_memory(
    memory_in: MemoryCreateUpdate,
    memory_service: MemoryService = Depends(get_memory_service),
    current_user_id: str = Depends(get_current_user_id),
):

    if(memory_in.user_id!=current_user_id):
        raise HTTPException(status_code=401, detail="Unable to save memory, user must be same")

    memory = memory_service.save_memory(
        memory_text=memory_in.memory,
        key=memory_in.key,
        user_id=memory_in.user_id,
        agent_id=memory_in.agent_id,
    )
    return memory
