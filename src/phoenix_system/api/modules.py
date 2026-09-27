from uuid import UUID
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

@router.post("/modules/{module_id}/enable")
def enable_system_module_endpoint(
    request: Request,
    module_id: UUID,
):
    from phoenix_system.services.modules import (
        enable_system_module,
    )

    return enable_system_module(
        request,
        module_id,
    )


@router.post("/modules/{module_id}/disable")
def disable_system_module_endpoint(
    request: Request,
    module_id: UUID,
):
    from phoenix_system.services.modules import (
        disable_system_module,
    )

    return disable_system_module(
        request,
        module_id,
    )


@router.post("/modules/{module_id}/retire")
def retire_system_module_endpoint(
    request: Request,
    module_id: UUID,
):
    from phoenix_system.services.modules import (
        retire_system_module,
    )

    return retire_system_module(
        request,
        module_id,
    )