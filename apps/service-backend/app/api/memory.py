from fastapi import APIRouter, Depends, status, HTTPException
from app.database import get_session
from datetime import datetime
from app.services.memory_service import MemoryService
from app.utils.ids import generate_unique_id
from app.schemas.memory import MemoryRead, MemoryCreateUpdate
from app.security import get_current_user_id
from .deps import get_memory_service

router = APIRouter()

@router.get("/", response_model=MemoryRead)
def read_memory(
    reference: str,
    memory_service: MemoryService = Depends(get_memory_service),
    current_user_id: str = Depends(get_current_user_id),
):
    memory = memory_service.get_memory(reference=reference, user_id=current_user_id)
    if not memory:
        return MemoryRead(memory='', id=generate_unique_id(), reference='', updated_at=datetime.now())
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
    return memory_service.save_memory(
        reference=memory_in.reference,
        memory_text=memory_in.memory,
        user_id=current_user_id
    )
