from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from app.database import get_session
from app.services.payment_service import PaymentService
from app.schemas.payment import PaymentResponse, PaymentRequest

from app.security import get_current_user_id
from .deps import get_payment_service

router = APIRouter()


@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    booking_id: Optional[str] = Query(default=None),
    reference_id: Optional[str] = Query(default=None),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user_id : str = Depends(get_current_user_id)
):
    return payment_service.list_payments(booking_id=booking_id, reference_id=reference_id, user_id=current_user_id)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payment_in: PaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user_id: str = Depends(get_current_user_id)
):
    return payment_service.create_payment(payment_in=payment_in, user_id=current_user_id)



@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
)
def get_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user_id: str = Depends(get_current_user_id)
):
    return payment_service.get(payment_id)
