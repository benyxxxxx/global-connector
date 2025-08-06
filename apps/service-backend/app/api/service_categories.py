from fastapi import APIRouter, Depends, status
from typing import List
from sqlmodel import Session, select
from app.database import get_session
from app.models.service_category import ServiceCategory
from app.schemas.service_category import ServiceCategoryCreate, ServiceCategoryResponse
from app.security import get_current_user_id

# The prefix and tags will be handled in router.py
# router = APIRouter(dependencies=[Depends(get_current_user_id)])
router = APIRouter()

@router.post("/", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_service_category(service_category: ServiceCategoryCreate, db: Session = Depends(get_session)):
    """
    Create a new service category.
    """
    # CORRECTED: Use ServiceCategory.from_orm
    db_service_category = ServiceCategory.model_validate(service_category)
    db.add(db_service_category)
    db.commit()
    db.refresh(db_service_category)
    return db_service_category

@router.get("/", response_model=List[ServiceCategoryResponse])
def list_service_categories(db: Session = Depends(get_session)): # CORRECTED: Function name
    """
    List all available service categories.
    """
    # CORRECTED: Select from ServiceCategory model
    service_categories = db.exec(select(ServiceCategory)).all()
    return service_categories