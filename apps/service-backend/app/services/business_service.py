from sqlmodel import Session
from typing import Optional, List
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate
from app.repositories.business_repository import BusinessRepository
from app.exceptions.business_exceptions import (
    BusinessNotFoundException,
    BusinessNameConflictException,
    UnauthorizedBusinessAccessException,
)


class BusinessService:
    def __init__(self, session: Session):
        self.repo = BusinessRepository(session)

    def create(self, business_in: BusinessCreate, owner_id: str) -> Business:
        """Create a new business"""

        # Check for name conflict within owner's businesses
        if self.repo.check_name_conflict(name=business_in.name, owner_id=owner_id):
            raise BusinessNameConflictException(business_in.name, owner_id)

        return self.repo.create(business_in=business_in, owner_id=owner_id)

    def get_by_id(self, business_id: str) -> Optional[Business]:
        """Get business by ID"""
        business = self.repo.get(business_id)

        if not business:
            raise BusinessNotFoundException(business_id)

        return business

    def get_all(self) -> List[Business]:
        """Get all businesses"""
        return self.repo.get_all()

    def get_by_owner_id(self, owner_id: str) -> List[Business]:
        """Get businesses by owner ID"""
        return self.repo.get_by_owner_id(owner_id=owner_id)

    def update(
        self, business_id: str, business_in: BusinessUpdate, current_user_id: str
    ) -> Business:
        """Update business"""
        business = self.repo.get(business_id)

        if not business:
            raise BusinessNotFoundException(business_id)

        if current_user_id != business.owner_id:
            raise UnauthorizedBusinessAccessException(business_id)

        return self.repo.update(business_id=business_id, business_in=business_in)

    def delete(self, business_id: str, current_user_id: str) -> bool:
        """Delete business"""
        business = self.repo.get(business_id)

        if not business:
            raise BusinessNotFoundException(business_id)

        if current_user_id != business.owner_id:
            raise UnauthorizedBusinessAccessException(business_id)

        return self.repo.delete(business_id=business_id)
