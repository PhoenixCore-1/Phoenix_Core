from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_system.services.users import (
    get_system_user,
    list_system_users,
)

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System Platform"],
)


@router.get("/users")
def system_users(request: Request, search: str = ""):
    return list_system_users(request, search)


@router.get("/users/{user_id}")
def system_user_detail(request: Request, user_id: UUID):
    return get_system_user(request, user_id)
 
@router.post("/users")
async def create_system_user_endpoint(request: Request):
    from phoenix_system.services.users import create_system_user

    return await create_system_user(request)

@router.post("/users/{user_id}/suspend")
def suspend_system_user_endpoint(request: Request, user_id: UUID):
    from phoenix_system.services.users import suspend_system_user

    return suspend_system_user(request, user_id)

@router.post("/users/{user_id}/reactivate")
def reactivate_system_user_endpoint(request: Request, user_id: UUID):
    from phoenix_system.services.users import reactivate_system_user

    return reactivate_system_user(request, user_id)

@router.post("/users/{user_id}/reset-password")
async def reset_system_user_password_endpoint(
    request: Request,
    user_id: UUID,
):
    from phoenix_system.services.users import reset_system_user_password

    return await reset_system_user_password(request, user_id)

@router.post("/users/{user_id}/require-password-reset")
def require_system_user_password_reset_endpoint(
    request: Request,
    user_id: UUID,
):
    from phoenix_system.services.users import require_system_user_password_reset

    return require_system_user_password_reset(request, user_id)
