from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_system.services.companies import (
    create_system_company,
    get_system_company,
    list_system_companies,
)

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System Platform"],
)


@router.get("/companies")
def system_companies(request: Request):
    return list_system_companies(request)


@router.get("/companies/{organisation_id}")
def system_company_detail(
    request: Request,
    organisation_id: UUID,
):
    return get_system_company(
        request,
        organisation_id,
    )


@router.post("/companies")
async def create_system_company_endpoint(
    request: Request,
):
    return await create_system_company(request)

@router.post("/companies/{organisation_id}/suspend")
def suspend_system_company_endpoint(
    request: Request,
    organisation_id: UUID,
):
    from phoenix_system.services.companies import (
        suspend_system_company,
    )

    return suspend_system_company(
        request,
        organisation_id,
    )


@router.post("/companies/{organisation_id}/activate")
def activate_system_company_endpoint(
    request: Request,
    organisation_id: UUID,
):
    from phoenix_system.services.companies import (
        activate_system_company,
    )

    return activate_system_company(
        request,
        organisation_id,
    )

@router.post(
    "/companies/{organisation_id}/modules/{module_code}/activate"
)
def activate_system_company_module_endpoint(
    request: Request,
    organisation_id: UUID,
    module_code: str,
):
    from phoenix_system.services.companies import (
        activate_system_company_module,
    )

    return activate_system_company_module(
        request,
        organisation_id,
        module_code,
    )


@router.post(
    "/companies/{organisation_id}/modules/{module_code}/suspend"
)
def suspend_system_company_module_endpoint(
    request: Request,
    organisation_id: UUID,
    module_code: str,
):
    from phoenix_system.services.companies import (
        suspend_system_company_module,
    )

    return suspend_system_company_module(
        request,
        organisation_id,
        module_code,
    )
from uuid import UUID
from fastapi import Request

from phoenix_system.services.companies import create_system_company_admin


@router.post("/companies/{organisation_id}/admin")
async def create_system_company_admin_endpoint(
    request: Request,
    organisation_id: UUID,
):
    return await create_system_company_admin(request, organisation_id)
