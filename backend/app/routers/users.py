"""User registration API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from backend.app.api.dependencies import get_user_service
from backend.app.api.schemas import ErrorResponse
from walletmind.schemas.user import UserCreateDTO, UserDTO, UserUpdateDTO
from walletmind.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

error_responses = {
    404: {"model": ErrorResponse, "description": "User not found"},
    409: {"model": ErrorResponse, "description": "Duplicate user"},
    422: {"model": ErrorResponse, "description": "Validation error"},
}


@router.post(
    "",
    response_model=UserDTO,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
def create_user(
    payload: UserCreateDTO,
    service: UserService = Depends(get_user_service),
) -> UserDTO:
    """Create a user profile."""

    return service.create_user(payload)


@router.get(
    "/{user_id}",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserDTO:
    """Fetch a user by UUID."""

    return service.get_user_by_uuid(user_id)


@router.put(
    "/{user_id}",
    response_model=UserDTO,
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def update_user(
    user_id: UUID,
    payload: UserUpdateDTO,
    service: UserService = Depends(get_user_service),
) -> UserDTO:
    """Update a user by UUID."""

    return service.update_user(user_id, payload)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses,
)
def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> Response:
    """Delete a user by UUID."""

    service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=list[UserDTO],
    status_code=status.HTTP_200_OK,
)
def list_users(service: UserService = Depends(get_user_service)) -> list[UserDTO]:
    """List all users."""

    return service.list_users()
