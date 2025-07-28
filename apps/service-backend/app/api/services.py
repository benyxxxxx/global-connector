from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from app.schemas.service import ServiceResponse, ServiceCreate, ServiceUpdate
from app.services.manage_service import ServiceManager
from app.security import get_current_user_id
from .deps import get_service_manager


router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.get("/", response_model=List[ServiceResponse])
def list_services(
    q: Optional[str] = Query(default=None, description="Search by name or description"),
    service_manager: ServiceManager = Depends(get_service_manager),
):
    return service_manager.list(q)


@router.get("/my", response_model=List[ServiceResponse])
async def get_owner_businesses(
    service_manager: ServiceManager = Depends(get_service_manager),
    current_user_id: str = Depends(get_current_user_id),
):
    return service_manager.list_by_owner_id(current_user_id)


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    service_manager: ServiceManager = Depends(get_service_manager),
    current_user_id: str = Depends(get_current_user_id),
):
    service = service_manager.create(service_in, current_user_id)
    return service


@router.get("/{service_id}", response_model=ServiceResponse)
def read_service(
    service_id: str, service_manager: ServiceManager = Depends(get_service_manager)
):
    service = service_manager.get(service_id)
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: str,
    service_in: ServiceUpdate,
    service_manager: ServiceManager = Depends(get_service_manager),
    current_user_id: str = Depends(get_current_user_id),
):
    service = service_manager.update(service_id, service_in, current_user_id)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    service_manager: ServiceManager = Depends(get_service_manager),
    current_user_id: str = Depends(get_current_user_id),
):
    service_manager.delete(service_id, current_user_id)
    return None
