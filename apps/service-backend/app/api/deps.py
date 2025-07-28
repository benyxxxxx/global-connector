from fastapi import Depends
from sqlmodel import Session

from app.services.business_service import BusinessService
from app.services.manage_service import ServiceManager
from app.services.booking_service import BookingService
from app.services.memory_service import MemoryService
from app.services.payment_service import PaymentService

from app.database import get_session
from app.security import get_current_user_id


def get_business_service(
    session: Session = Depends(get_session),
) -> BusinessService:
    return BusinessService(session)


def get_service_manager(
    session: Session = Depends(get_session),
) -> ServiceManager:
    return ServiceManager(session)


def get_booking_service(
    session: Session = Depends(get_session),
) -> BookingService:
    return BookingService(session)

def get_memory_service(
    session: Session = Depends(get_session),
) -> MemoryService:
    return MemoryService(session)


def get_payment_service(
    session: Session = Depends(get_session),
) -> PaymentService:
    return PaymentService(session)
