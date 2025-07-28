from fastapi import HTTPException, status


class BusinessNotFoundException(HTTPException):
    def __init__(self, business_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with id {business_id} not found",
        )


class BusinessNameConflictException(HTTPException):
    def __init__(self, name: str, owner_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Business with name '{name}' already exists for owner {owner_id}",
        )


class UnauthorizedBusinessAccessException(HTTPException):
    def __init__(self, business_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access business {business_id}",
        )
