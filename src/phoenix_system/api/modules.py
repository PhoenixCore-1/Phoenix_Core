from fastapi import APIRouter, Request

from phoenix_system.services.modules import (
    list_system_modules,
)

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System Platform"],
)


@router.get("/modules")
def system_modules(request: Request):
    return list_system_modules(request)
