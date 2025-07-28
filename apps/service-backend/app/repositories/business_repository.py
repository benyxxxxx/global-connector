from sqlmodel import Session, select, and_
from datetime import timezone
from typing import Optional, List
from datetime import datetime
from app.utils.ids import generate_unique_id
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate


class BusinessRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, business_in: BusinessCreate, owner_id: str):
        """Create a new business"""

        business_id = generate_unique_id()

        business_data = business_in.model_dump()
        business = Business(
            id=business_id,
            owner_id=owner_id,
            **business_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(business)
        self.session.commit()
        self.session.refresh(business)
        return business

    def check_name_conflict(self, name: str, owner_id: str) -> bool:
        """Check if business name already exists for the owner"""

        statement = select(Business).where(
            and_(Business.name == name, Business.owner_id == owner_id)
        )

        existing_business = self.session.exec(statement).first()

        return existing_business is not None

    def get(self, business_id: str) -> Optional[Business]:
        """Get business by ID"""

        statement = select(Business).where(Business.id == business_id)

        return self.session.exec(statement).first()

    def get_all(self) -> List[Business]:
        """Get all businesses"""

        statement = select(Business)
        statement = statement.order_by(Business.created_at.desc())

        return self.session.exec(statement).all()

    def get_by_owner_id(self, owner_id: str) -> List[Business]:
        """Get businesses by owner ID"""

        statement = (
            select(Business)
            .where(Business.owner_id == owner_id)
            .order_by(Business.created_at.desc())
        )

        return self.session.exec(statement).all()

    def update(
        self, business_id: str, business_in: BusinessUpdate
    ) -> Optional[Business]:
        """Update business"""

        business = self.get(business_id)

        if not business:
            return None  # or raise a custom exception

        update_data = business_in.model_dump(exclude_unset=True)

        # Apply updates
        for field, value in update_data.items():
            setattr(business, field, value)

        business.updated_at = datetime.now(timezone.utc)

        self.session.add(business)
        self.session.commit()
        self.session.refresh(business)

        return business

    def delete(self, business_id: str) -> bool:
        """Delete business"""

        business = self.get(business_id)

        if not business:
            return False

        self.session.delete(business)
        self.session.commit()
        return True
