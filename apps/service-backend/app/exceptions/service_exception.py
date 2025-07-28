from fastapi import HTTPException, status


class ServiceAlreadyExistsException(HTTPException):
    def __init__(self, name: str, business_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service {name} for business {business_id} already exists",
        )


class ServiceNotFoundException(HTTPException):
    def __init__(self, service_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with id {service_id} not found",
        )


class ServiceNameConflictException(HTTPException):
    def __init__(self, name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service with name '{name}' already exists",
        )


class UnauthorizedServiceAccessException(HTTPException):
    def __init__(self, service_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access service {service_id}",
        )
