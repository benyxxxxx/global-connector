from urllib.parse import urlencode, quote
from typing import List, Optional
from decimal import Decimal
from app.repositories.payment_repository import PaymentRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.service_repository import ServiceRepository
from app.exceptions.booking_exception import BookingNotFoundException
from app.utils.ids import generate_random_base58_key
from app.schemas.payment import (
    PaymentCreate,
    PaymentBase,
    PaymentRequest,
    PaymentUpdate,
    PaymentStatus,
    PaymentMethod,
)
from app.config import settings
from sqlmodel import Session
from app.exceptions.payment_exceptions import (
    PaymentNotFoundException,
    UnauthorizedPaymentAccessException,
)
from app.services.solana_service import verify_payment
from app.models.payment import Payment, PaymentProvider


class PaymentService:
    def __init__(self, session: Session):
        self.repo = PaymentRepository(session)
        self.booking_repo = BookingRepository(session)
        self.service_repo = ServiceRepository(session)


    def verify_payment_status(self, payment_id: str):
        payment_data = self.repo.get(payment_id=payment_id)

        ref = payment_data.external_id

        status = False
        signature = ''

        try:
            status, signature = verify_payment(
                reference_key=ref, expected_amount=payment_data.amount, token_mint=settings.MANDEL_COIN_MINT_ADDRESS)
        except Exception as e:
            raise Exception(e)

        if status:
            payment_data.status = PaymentStatus.SUCCEEDED

            meta = payment_data.payment_metadata or {}
            meta['signature'] = signature

            self.repo.update(
                payment_id=payment_id,
                payment_in=PaymentUpdate(
                    status=payment_data.status,
                    payment_metadata=meta
                )
            )

        
    def get(self, payment_id: str) -> Payment:
        self.verify_payment_status(payment_id)
        payment_data = self.repo.get(payment_id=payment_id)

        if not payment_data:
            raise PaymentNotFoundException(payment_id)

        return payment_data

    def list_payments(
        self,
        booking_id: Optional[str] = None,
        reference_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Payment]:
        return self.repo.list_payments(user_id=user_id, booking_id=booking_id, reference_id=reference_id)

    def get_payment_provider(self, method: PaymentMethod):
        if method == PaymentMethod.MANDEL_COIN:
            return PaymentProvider.SOLANA
        return ""

    def get_solana_address(self):
        return {
            "destination": settings.SOLANA_DESTINATION_ADDRESS,
            "mint": settings.MANDEL_COIN_MINT_ADDRESS,
        }

    def generate_solana_pay_url(
        self,
        amount: float,
        reference: str,
        label: str = None,
        message: str = None,
        memo: str = None,
    ) -> str:
        base = f"solana:{settings.SOLANA_DESTINATION_ADDRESS}"

        params = {}

        if amount is not None:
            params["amount"] = str(amount)
        if reference:
            params["reference"] = reference
        if label:
            params["label"] = label
        if message:
            params["message"] = message
        if memo:
            params["memo"] = memo

        params["spl-token"] = settings.MANDEL_COIN_MINT_ADDRESS

        query = urlencode(params, quote_via=quote)

        return f"{base}?{query}" if query else base

    def get_payment_meta_for(self, method: PaymentMethod):
        if method == PaymentMethod.MANDEL_COIN:
            return self.get_solana_address()
        return {}

    def create_payment(
        self,
        payment_in: PaymentRequest,
        user_id: str
    ) -> Payment:
        # Case 1: Linked to a Booking
        if payment_in.booking_id:
            resolved_booking_id = payment_in.booking_id
            booking = self.booking_repo.get(resolved_booking_id)
            if not booking:
                raise BookingNotFoundException(resolved_booking_id)

            amount = booking.total_price or 0
            currency = booking.service.currency

            # Check for existing payments
            payments = self.repo.list_payments(booking_id=resolved_booking_id)
            if payments and not payment_in.force_add:
                return payments[0]

        # Case 2: Custom reference-based payment
        elif payment_in.reference_id:
            amount = Decimal(payment_in.amount)
            currency = "USD"  # or pass currency in PaymentRequest if needed

        else:
            raise ValueError(
                "Either booking_id or (reference_id and reference_type) must be provided.")

        # Create payment meta
        reference = generate_random_base58_key()
        payment_meta = self.get_payment_meta_for(payment_in.payment_method)
        payment_meta["solana_pay_link"] = self.generate_solana_pay_url(
            amount, reference)

        # Build payment data
        payment_data = PaymentCreate(
            amount=amount,
            status=PaymentStatus.PENDING,
            currency=currency,
            transaction_id="",
            external_id=reference,
            payment_method=payment_in.payment_method,
            payment_metadata=payment_meta,
            provider=self.get_payment_provider(payment_in.payment_method),
            reference_id=payment_in.reference_id,
            reference_type=payment_in.reference_type,
        )

        # Save payment
        payment_created = self.repo.create(
            payment_in=payment_data,
            booking_id=payment_in.booking_id,  # Optional,
            user_id=user_id
        )

        return payment_created
