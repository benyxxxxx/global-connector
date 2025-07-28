from typing import List, Optional
from sqlmodel import select, Session, and_, or_
from datetime import datetime, timezone
from app.utils.ids import generate_unique_id
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


class ServiceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, service_id: str) -> Optional[Service]:
        statement = select(Service).where(Service.id == service_id)
        service = self.session.exec(statement).first()
        return service

    def list(self, search: Optional[str] = None) -> List[Service]:
        statement = select(Service)

        if search:
            keyword = f"%{search}%"
            statement = statement.where(
                or_(
                    Service.name.ilike(keyword),
                    Service.description.ilike(keyword)
                )
            )

        return self.session.exec(statement).all()

    # def list_by_business(self, business_id: str) -> List[Service]:
    #     statement = select(Service).where(Service.business_id == business_id)
    #     return self.session.exec(statement).all()

    def list_by_owner_id(self, owner_id: str) -> List[Service]:
        """List service by owner ID"""
        statement = (
            select(Service)
            .where()
            .where(Service.owner_id == owner_id)
            .order_by(Service.created_at.desc())
        )
        return self.session.exec(statement).all()

    def check_name_conflict(
        self, name: str, owner_id: str, business_id: str = ""
    ) -> bool:
        """Check if service name already exists for the business"""
        statement = select(Service)

        # if business_id:
        #     statement = statement.where(
        #     and_(Service.name == name, Service.business_id == business_id)
        # )

        if owner_id:
            statement = statement.where(
                and_(Service.name == name, Service.owner_id == owner_id)
            )

        existing_service = self.session.exec(statement).first()
        return existing_service is not None

    def create(self, service_in: ServiceCreate, owner_id: str) -> Service:

        service_id = generate_unique_id()
        service_data = service_in.model_dump(mode="json")

        service = Service(
            id=service_id,
            owner_id=owner_id,
            **service_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(service)
        self.session.commit()
        self.session.refresh(service)
        return service

    def update(self, service_id: str, service_in: ServiceUpdate) -> Service:
        service = self.get(service_id)

        for field, value in service_in.model_dump(
            exclude_unset=True, mode="json"
        ).items():
            if field == "attributes":
                setattr(service, "attributes", value)
            else:
                setattr(service, field, value)

        service.updated_at = datetime.now(timezone.utc)
        self.session.add(service)
        self.session.commit()
        self.session.refresh(service)
        return service

    def delete(self, service_id: str) -> None:
        service = self.get(service_id)
        self.session.delete(service)
        self.session.commit()
