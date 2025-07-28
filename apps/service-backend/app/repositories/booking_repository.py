from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_
from app.utils.ids import generate_unique_id
from fastapi.encoders import jsonable_encoder
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate, BookingCreateValidated
from app.models.service import Service


class BookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, booking_id: str) -> Booking:
        statement = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.service))
        )
        booking = self.session.exec(statement).first()
        return booking

    def list_by_user(self, user_id: str) -> List[Booking]:
        statement = select(Booking).where(Booking.user_id == user_id)
        return self.session.exec(statement).all()

    def create(self, booking_in: BookingCreateValidated, user_id: str) -> Booking:

        service_snapshot = self.session.get(Service, booking_in.service_id)
        snapshot = jsonable_encoder(service_snapshot)

        booking_id = generate_unique_id()
        booking_data = booking_in.model_dump()

        booking = Booking(
            id=booking_id,
            user_id=user_id,
            service_snapshot=snapshot,
            **booking_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking

    def update(self, booking_id: str, booking_in: BookingUpdate) -> Booking:
        booking = self.get(booking_id)

        for key, value in booking_in.model_dump(exclude_unset=True).items():
            setattr(booking, key, value)

        booking.updated_at = datetime.now(timezone.utc)
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return booking

    def check_booking_conflict(
        self, user_id: str, service_id: str, scheduled_at: datetime
    ):
        # Check for duplicate bookings by same user for overlapping scheduled time
        existing_booking = self.session.exec(
            select(Booking).where(
                and_(
                    Booking.user_id == user_id,
                    Booking.service_id == service_id,
                    Booking.scheduled_at == scheduled_at,
                    Booking.status != "cancelled",
                )
            )
        ).first()
        return existing_booking is not None

    def delete(self, booking_id: str) -> None:
        booking = self.get(booking_id)
        self.session.delete(booking)
        self.session.commit()
