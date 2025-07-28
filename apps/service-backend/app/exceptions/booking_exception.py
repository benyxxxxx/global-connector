from fastapi import HTTPException, status


class BookingAlreadyExistsException(HTTPException):
    def __init__(self, name: str, service_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking {name} for service {service_id} already exists",
        )


class BookingNotFoundException(HTTPException):
    def __init__(self, booking_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} not found",
        )


class BookingConflictException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a booking for this service at the scheduled time.",
        )


class UnauthorizedBookingAccessException(HTTPException):
    def __init__(self, booking_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access Booking {booking_id}",
        )


class BookingTimeBasedDurationRequiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duration is required for time-based pricing.",
        )


class BookingInvalidTimeBasedConfigurationException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time-based pricing configuration on service.",
        )


class BookingInvalidDurationException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking duration must be a positive number for time-based pricing.",
        )
