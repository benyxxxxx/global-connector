from typing import List, Optional
from sqlmodel import Session
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.exceptions.service_exception import (
    ServiceAlreadyExistsException,
    ServiceNotFoundException,
    UnauthorizedServiceAccessException,
)
from app.repositories.service_repository import ServiceRepository


class ServiceManager:
    def __init__(self, session: Session):
        self.repo = ServiceRepository(session)

    def get(self, service_id: str) -> Optional[Service]:
        service = self.repo.get(service_id)

        if not service:
            raise ServiceNotFoundException(service_id)

        return service

    def list(self, search: Optional[str]) -> List[Service]:
        return self.repo.list(search)

    def list_by_owner_id(self, owner_id: str) -> List[Service]:
        return self.repo.list_by_owner_id(owner_id=owner_id)

    def create(self, service_in: ServiceCreate, owner_id: str) -> Service:
        if self.repo.check_name_conflict(service_in.name, owner_id=owner_id):
            raise ServiceAlreadyExistsException(service_in.name, owner_id)

        return self.repo.create(service_in=service_in, owner_id=owner_id)

    def update(
        self, service_id: str, service_in: ServiceUpdate, current_user_id: str
    ) -> Service:
        service = self.repo.get(service_id)

        if not service:
            raise ServiceNotFoundException(service_id)

        if service.owner_id != current_user_id:
            raise UnauthorizedServiceAccessException(service_id)

        return self.repo.update(service_id=service_id, service_in=service_in)

    def delete(self, service_id: str, current_user_id: str) -> None:
        service = self.repo.get(service_id)

        if not service:
            raise ServiceNotFoundException(service_id)

        if service.owner_id != current_user_id:
            raise UnauthorizedServiceAccessException(service_id)

        return self.repo.delete(service_id)
