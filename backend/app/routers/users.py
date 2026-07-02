"""User registration API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.app.api.dependencies import get_user_service
from backend.app.api.schemas import ErrorResponse
from backend.app.schemas.response import ApiResponse, DeleteUserStatusData
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
    response_model=ApiResponse[UserDTO],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses,
)
def create_user(
    payload: UserCreateDTO,
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserDTO]:
    """Create a user profile."""

    user = service.create_user(payload)
    return ApiResponse(message="User created successfully.", data=user)


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserDTO],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserDTO]:
    """Fetch a user by UUID."""

    user = service.get_user_by_uuid(user_id)
    return ApiResponse(message="User retrieved successfully.", data=user)


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserDTO],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def update_user(
    user_id: UUID,
    payload: UserUpdateDTO,
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserDTO]:
    """Update a user by UUID."""

    user = service.update_user(user_id, payload)
    return ApiResponse(message="User updated successfully.", data=user)


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[DeleteUserStatusData],
    status_code=status.HTTP_200_OK,
    responses=error_responses,
)
def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> ApiResponse[DeleteUserStatusData]:
    """Delete a user by UUID."""

    service.delete_user(user_id)
    return ApiResponse(
        message="User deleted successfully.",
        data=DeleteUserStatusData(user_uuid=str(user_id)),
    )


@router.get(
    "",
    response_model=ApiResponse[list[UserDTO]],
    status_code=status.HTTP_200_OK,
)
def list_users(service: UserService = Depends(get_user_service)) -> ApiResponse[list[UserDTO]]:
    """List all users."""

    users = service.list_users()
    return ApiResponse(message="Users retrieved successfully.", data=users)
