from typing import List
from sqlmodel import Session
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate, BookingCreateValidated
from app.schemas.service import ServiceBase, PricingType
from app.exceptions.booking_exception import (
    BookingNotFoundException,
    BookingConflictException,
    BookingInvalidDurationException,
    BookingTimeBasedDurationRequiredException,
    BookingInvalidTimeBasedConfigurationException,
    UnauthorizedBookingAccessException,
)
from app.exceptions.service_exception import ServiceNotFoundException
from app.repositories.booking_repository import BookingRepository
from app.repositories.service_repository import ServiceRepository


class BookingService:
    def __init__(self, session: Session):
        self.repo = BookingRepository(session)
        self.service_repo = ServiceRepository(session)

    def get(self, booking_id: str, user_id: str) -> Booking:
        booking = self.repo.get(booking_id=booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)

        if booking.user_id != user_id:
            raise UnauthorizedBookingAccessException(booking_id=booking_id)

        return booking

    def list_user_bookings(self, current_user_id: str) -> List[Booking]:
        return self.repo.list_by_user(user_id=current_user_id)

    def calculate_total_price(self, service: ServiceBase, booking: BookingCreate) -> float:
        """
        Calculate the total price for a booking based on the service pricing model.

        Args:
            service (ServiceBase): The service object containing pricing info.
            booking (BookingCreate): The booking details, including duration if needed.

        Returns:
            float: The total calculated price.
        """

        # Defensive check for duration in time-based pricing
        if service.pricing_model == PricingType.TIME_BASED:
            if not booking.duration or booking.duration <= 0:
                raise BookingInvalidDurationException()
            return service.base_price * booking.duration

        # Extend here for other pricing models in the future
        # e.g. if service.pricing_model == PricingType.FLAT_FEE:
        #           return service.base_price
        # or if service.pricing_model == PricingType.PER_UNIT:
        #           return service.base_price * booking.units

        return service.base_price


    def create(self, booking_in: BookingCreate, current_user_id: str) -> Booking:
        service = self.service_repo.get(booking_in.service_id)

        if not service:
            raise ServiceNotFoundException(booking_in.service_id)

        if self.repo.check_booking_conflict(
            user_id=current_user_id,
            service_id=service.id,
            scheduled_at=booking_in.scheduled_at,
        ):
            raise BookingConflictException()

        pricing_model = service.pricing_model
        base_price = service.base_price
        time_unit = service.time_unit

        # Validate and compute price
        if pricing_model == "time_based":
            if booking_in.duration is None:
                raise BookingTimeBasedDurationRequiredException()
            if base_price is None or time_unit is None:
                raise BookingInvalidTimeBasedConfigurationException()
        
        base_price = service.base_price
        total_price = self.calculate_total_price(service=service, booking=booking_in)
        booking_in_validated = BookingCreateValidated(base_price=base_price, total_price=total_price, **booking_in.model_dump())

        return self.repo.create(booking_in=booking_in_validated, user_id=current_user_id)

    def update(
        self, booking_id: str, booking_in: BookingUpdate, current_user_id: str
    ) -> Booking:
        booking = self.repo.get(booking_id)

        if not booking:
            raise BookingNotFoundException(booking_id)

        if booking.user_id != current_user_id:
            raise UnauthorizedBookingAccessException(booking_id)

        return self.repo.update(booking_id=booking_id, booking_in=booking_in)

    def delete(self, booking_id: str, current_user_id: str) -> None:
        booking = self.repo.get(booking_id)

        if not booking:
            raise BookingNotFoundException(booking_id)

        if booking.user_id != current_user_id:
            raise UnauthorizedBookingAccessException(booking_id)

        return self.repo.delete(booking_id=booking_id)
