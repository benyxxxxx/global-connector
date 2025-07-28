# app/api/bookings.py
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from app.security import get_current_user_id
from .deps import get_booking_service

router = APIRouter()


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_in: BookingCreate,
    booking_service: BookingService = Depends(get_booking_service),
    current_user_id: str = Depends(get_current_user_id),
):
    return booking_service.create(
        booking_in=booking_in, current_user_id=current_user_id
    )


@router.get("/", response_model=List[BookingResponse])
def list_my_bookings(
    booking_service: BookingService = Depends(get_booking_service),
    current_user_id: str = Depends(get_current_user_id),
):
    return booking_service.list_user_bookings(current_user_id=current_user_id)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
    current_user_id: str = Depends(get_current_user_id),
):
    return booking_service.get(booking_id=booking_id, user_id=current_user_id)


@router.patch("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: str,
    booking_in: BookingUpdate,
    booking_service: BookingService = Depends(get_booking_service),
    current_user_id: str = Depends(get_current_user_id),
):
    return booking_service.update(
        booking_id=booking_id,
        booking_in=booking_in,
        current_user_id=current_user_id,
    )


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service),
    current_user_id: str = Depends(get_current_user_id),
):
    booking_service.delete(booking_id=booking_id, current_user_id=current_user_id)
    return None
