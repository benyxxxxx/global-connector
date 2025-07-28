from fastapi import APIRouter, Depends, status
from typing import List
from app.schemas.business import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
)
from app.services.business_service import BusinessService
from app.api.deps import get_business_service
from app.security import get_current_user_id

router = APIRouter(dependencies=[Depends(get_current_user_id)])


@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_in: BusinessCreate,
    business_service: BusinessService = Depends(get_business_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """Create a new business"""
    return business_service.create(business_in, current_user_id)


@router.get("/", response_model=List[BusinessResponse])
async def get_businesses(
    business_service: BusinessService = Depends(get_business_service),
):
    """Get all businesses with optional filtering"""
    return business_service.get_all()


@router.get("/my", response_model=List[BusinessResponse])
async def get_owner_businesses(
    business_service: BusinessService = Depends(get_business_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """Get businesses by owner ID"""
    return business_service.get_by_owner_id(current_user_id)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str, business_service: BusinessService = Depends(get_business_service)
):
    """Get business by ID"""
    return business_service.get_by_id(business_id)


@router.put("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    business_update: BusinessUpdate,
    business_service: BusinessService = Depends(get_business_service),
    current_user_id: str = Depends(get_current_user_id),
):
    """Update business by ID"""
    return business_service.update(
        business_id=business_id,
        business_in=business_update,
        current_user_id=current_user_id,
    )


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
):
    return business_service.delete(business_id)
