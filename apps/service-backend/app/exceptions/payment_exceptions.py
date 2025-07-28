from fastapi import HTTPException, status


class PaymentAlreadyExistsException(HTTPException):
    def __init__(self, name: str, business_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment {name} for business {business_id} already exists",
        )


class PaymentNotFoundException(HTTPException):
    def __init__(self, payment_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with id {payment_id} not found",
        )


class PaymentNameConflictException(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment with name '{name}' already exists",
        )


class UnauthorizedPaymentAccessException(HTTPException):
    def __init__(self, payment_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access Payment {payment_id}",
        )
