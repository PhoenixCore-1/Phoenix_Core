"""Phoenix Core V1.0.0 baseline platform endpoints.

This is intentionally small: it proves the SaaS shell end-to-end without
making the existing role/permission framework part of the baseline UX.
"""
from uuid import UUID, uuid4
from fastapi import APIRouter, Request
from phoenix_core.errors import AuthenticationError, AuthorizationError, ValidationError

router = APIRouter(prefix="/api/v1/baseline", tags=["Phoenix Core V1 Baseline"])

def _session_context(request: Request):
    api = request.app.state.core_api
    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthenticationError("Authentication required.")
    sid = api.resolve_session_id(token)
    row = api.db.execute(
        "SELECT u.id, u.identity_id, u.username, u.display_name, u.status, u.platform_level "
        "FROM users u JOIN sessions s ON s.identity_id=u.identity_id WHERE s.id=?",
        (str(sid),),
    ).fetchone()
    if not row:
        raise AuthenticationError("User session is not valid.")
    org = api.db.execute(
        "SELECT o.id,o.code,o.name,o.status FROM organisations o "
        "JOIN organisation_memberships m ON m.organisation_id=o.id "
        "WHERE m.identity_id=? AND m.status='ACTIVE' AND o.status='ACTIVE' LIMIT 1",
        (row["identity_id"],),
    ).fetchone()
    return api, row, org


def _audit_system_user(
    request: Request,
    api,
    user,
    org,
    *,
    action: str,
    target_id,
):
    """Record a system-user administrative action in Core audit."""
    token = request.cookies.get("phoenix_session")
    session_id = api.resolve_session_id(token)

    context = api.resolve_context(
        request_id=str(
            getattr(request.state, "request_id", None)
            or uuid4()
        ),
        session_id=session_id,
        organisation_id=(
            org["id"]
            if org is not None
            else None
        ),
    )

    api._audit(
        context,
        action=action,
        target_type="USER",
        target_id=UUID(str(target_id)),
    )
@router.get("/system/users")
def system_users(request: Request, search: str = ""):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    search = search.strip()
    if search:
        rows = api.db.execute(
            "SELECT u.id,u.identity_id,u.username,u.display_name,u.status,"
            "u.platform_level,u.password_reset_required,u.created_at "
            "FROM users u "
            "WHERE u.platform_level='SYSTEM_ADMIN' "
            "AND (u.username LIKE ? OR u.display_name LIKE ?) "
            "ORDER BY u.display_name",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = api.db.execute(
            "SELECT u.id,u.identity_id,u.username,u.display_name,u.status,"
            "u.platform_level,u.password_reset_required,u.created_at "
            "FROM users u "
            "WHERE u.platform_level='SYSTEM_ADMIN' "
            "ORDER BY u.display_name"
        ).fetchall()

    return {"data": {"items": [dict(r) for r in rows]}}


@router.get("/system/users/{user_id}")
def system_user_detail(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    target = api.db.execute(
        "SELECT id,identity_id,username,display_name,status,"
        "platform_level,password_reset_required,created_at "
        "FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    return {"data": dict(target)}


@router.post("/system/users")
async def create_system_user(request: Request):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    payload = await request.json()
    username = str(payload.get("username", "")).strip()
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not display_name or len(password) < 12:
        raise ValidationError(
            "Username, display name and a password of at least 12 characters are required."
        )

    created = api.core_service.create_user(
        username,
        display_name,
        password,
    )

    api.db.execute(
        "UPDATE users SET platform_level='SYSTEM_ADMIN' WHERE id=?",
        (str(created.id),),
    )
    api.db.commit()

    return {
        "data": {
            "id": str(created.id),
            "identity_id": str(created.identity_id),
            "username": created.username,
            "display_name": created.display_name,
            "status": created.status,
            "platform_level": "SYSTEM_ADMIN",
            "password_reset_required": 0,
        }
    }


@router.post("/system/users/{user_id}/suspend")
def suspend_system_user(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    if str(user["id"]) == str(user_id):
        raise ValidationError("A system administrator cannot suspend their own account.")

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.core_service.suspend_user(user_id)
    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_SUSPENDED",
        target_id=user_id,
    )

    return {"data": {"id": str(user_id), "status": "SUSPENDED"}}


@router.post("/system/users/{user_id}/reactivate")
def reactivate_system_user(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.core_service.reactivate_user(user_id)
    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_REACTIVATED",
        target_id=user_id,
    )

    return {"data": {"id": str(user_id), "status": "ACTIVE"}}


@router.post("/system/users/{user_id}/reset-password")
async def reset_system_user_password(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    payload = await request.json()
    password = str(payload.get("password", ""))

    api.authentication_service.admin_reset_password(user_id, password)
    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_PASSWORD_RESET",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "password_reset_required": 1,
        }
    }


@router.post("/system/users/{user_id}/require-password-reset")
def require_system_user_password_reset(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.authentication_service.require_password_reset(user_id)
    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_PASSWORD_RESET_REQUIRED",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "password_reset_required": 1,
        }
    }

def _modules(api, org_id=None):
    rows = api.db.execute(
        "SELECT m.id,m.code,m.name,m.version,m.status, "
        "CASE WHEN e.status='ACTIVE' THEN 1 ELSE 0 END AS active "
        "FROM modules m LEFT JOIN module_entitlements e "
        "ON e.module_id=m.id AND e.organisation_id=? "
        "WHERE m.status='ENABLED' ORDER BY m.name",
        (str(org_id) if org_id else "",),
    ).fetchall()
    return [{"id":r["id"],"code":r["code"],"name":r["name"],"version":r["version"],"active":bool(r["active"])} for r in rows]

@router.get("/context")
def context(request: Request):
    api, user, org = _session_context(request)
    return {"data": {
        "user": {"id":user["id"],"username":user["username"],"display_name":user["display_name"],"platform_level":user["platform_level"]},
        "company": None if not org else {"id":org["id"],"code":org["code"],"name":org["name"],"status":org["status"]},
        "modules": _modules(api, org["id"] if org else None),
    }}

@router.get("/companies")
def companies(request: Request):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")
    rows = api.db.execute("SELECT id,code,name,status,created_at FROM organisations ORDER BY name").fetchall()
    return {"data":{"items":[dict(r) for r in rows]}}

@router.get("/companies/{organisation_id}")
def company_detail(request: Request, organisation_id: UUID):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    company = api.db.execute(
        "SELECT id,code,name,status,created_at,"
        "legal_name,trading_name,registration_number,tax_number,"
        "primary_email,telephone,website,"
        "address_line_1,address_line_2,city,province,postal_code,country,"
        "industry,company_type "
        "FROM organisations WHERE id=?",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found.")

    modules = api.db.execute(
        "SELECT m.id,m.code,m.name,m.version,m.status AS module_status,"
        "e.status AS entitlement_status "
        "FROM modules m "
        "LEFT JOIN module_entitlements e "
        "ON e.module_id=m.id AND e.organisation_id=? "
        "WHERE m.status='ENABLED' "
        "ORDER BY m.name",
        (str(organisation_id),),
    ).fetchall()

    module_items = []
    for row in modules:
        module_items.append({
            "id": row["id"],
            "code": row["code"],
            "name": row["name"],
            "version": row["version"],
            "status": row["entitlement_status"] or "NOT_ACTIVATED",
        })

    return {
        "data": {
            "company": dict(company),
            "modules": module_items,
        }
    }

@router.post("/companies")
async def create_company(request: Request):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")
    payload=await request.json()
    code=str(payload.get("code","")).strip().upper()
    name=str(payload.get("name","")).strip()
    if not code or not name:
        raise ValidationError("Company code and name are required.")

    company=api.core_service.create_organisation(code,name)

    registration_fields = {
        "legal_name": str(payload.get("legal_name","")).strip() or None,
        "trading_name": str(payload.get("trading_name","")).strip() or None,
        "registration_number": str(payload.get("registration_number","")).strip() or None,
        "tax_number": str(payload.get("tax_number","")).strip() or None,
        "primary_email": str(payload.get("primary_email","")).strip() or None,
        "telephone": str(payload.get("telephone","")).strip() or None,
        "website": str(payload.get("website","")).strip() or None,
        "address_line_1": str(payload.get("address_line_1","")).strip() or None,
        "address_line_2": str(payload.get("address_line_2","")).strip() or None,
        "city": str(payload.get("city","")).strip() or None,
        "province": str(payload.get("province","")).strip() or None,
        "postal_code": str(payload.get("postal_code","")).strip() or None,
        "country": str(payload.get("country","")).strip() or None,
        "industry": str(payload.get("industry","")).strip() or None,
        "company_type": str(payload.get("company_type","")).strip() or None,
    }

    api.db.execute(
        """
        UPDATE organisations
        SET legal_name=?,
            trading_name=?,
            registration_number=?,
            tax_number=?,
            primary_email=?,
            telephone=?,
            website=?,
            address_line_1=?,
            address_line_2=?,
            city=?,
            province=?,
            postal_code=?,
            country=?,
            industry=?,
            company_type=?
        WHERE id=?
        """,
        (
            registration_fields["legal_name"],
            registration_fields["trading_name"],
            registration_fields["registration_number"],
            registration_fields["tax_number"],
            registration_fields["primary_email"],
            registration_fields["telephone"],
            registration_fields["website"],
            registration_fields["address_line_1"],
            registration_fields["address_line_2"],
            registration_fields["city"],
            registration_fields["province"],
            registration_fields["postal_code"],
            registration_fields["country"],
            registration_fields["industry"],
            registration_fields["company_type"],
            str(company.id),
        ),
    )
    api.db.commit()

    return {
        "data": {
            "id":str(company.id),
            "code":company.code,
            "name":company.name,
            "status":company.status,
            **registration_fields,
        }
    }

@router.get("/modules")
def modules(request: Request):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")
    rows=api.db.execute("SELECT id,code,name,version,status FROM modules ORDER BY name").fetchall()
    return {"data":{"items":[dict(r) for r in rows]}}


@router.post("/companies/{organisation_id}/suspend")
def suspend_company(request: Request, organisation_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    company = api.db.execute(
        "SELECT id FROM organisations WHERE id=?",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found.")

    updated = api.core_service.suspend_organisation(
        organisation_id
    )

    return {
        "data": {
            "id": str(updated.id),
            "status": updated.status,
        }
    }


@router.post("/companies/{organisation_id}/activate")
def activate_company(request: Request, organisation_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    company = api.db.execute(
        "SELECT id FROM organisations WHERE id=?",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found.")

    updated = api.core_service.activate_organisation(
        organisation_id
    )

    return {
        "data": {
            "id": str(updated.id),
            "status": updated.status,
        }
    }

@router.post("/companies/{organisation_id}/modules/{module_code}/activate")
def activate_module(request: Request, organisation_id: UUID, module_code: str):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")
    module=api.db.execute("SELECT id,code,name,version,status FROM modules WHERE code=?", (module_code,)).fetchone()
    if not module:
        raise ValidationError("Module not found.")
    company=api.db.execute("SELECT id FROM organisations WHERE id=? AND status='ACTIVE'", (str(organisation_id),)).fetchone()
    if not company:
        raise ValidationError("Company not found or inactive.")
    module_id = UUID(module["id"])

    ent = api.core_service.get_organisation_module_entitlement(
        organisation_id,
        module_id,
    )

    if ent:
        if ent.status == "ACTIVE":
            raise ValidationError(
                "Organisation is already entitled to this module."
            )

        ent = api.core_service.activate_module_entitlement(
            ent.id
        )
    else:
        ent = api.core_service.grant_module_entitlement(
            organisation_id,
            module_id,
        )

    return {
        "data": {
            "company_id": str(organisation_id),
            "module_code": module_code,
            "entitlement_id": str(ent.id),
            "status": ent.status,
        }
    }


@router.post("/companies/{organisation_id}/modules/{module_code}/suspend")
def suspend_module(request: Request, organisation_id: UUID, module_code: str):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    module = api.db.execute(
        "SELECT id FROM modules WHERE code=?",
        (module_code,),
    ).fetchone()

    if not module:
        raise ValidationError("Module not found.")

    entitlement = api.core_service.get_organisation_module_entitlement(
        organisation_id,
        UUID(module["id"]),
    )

    if not entitlement:
        raise ValidationError("Module is not activated for this company.")

    updated = api.core_service.suspend_module_entitlement(entitlement.id)

    return {
        "data": {
            "company_id": str(organisation_id),
            "module_code": module_code,
            "entitlement_id": str(updated.id),
            "status": updated.status,
        }
    }
@router.get("/company/users")
def company_users(request: Request):
    api, user, org = _session_context(request)
    if user["platform_level"] not in ("COMPANY_ADMIN","SYSTEM_ADMIN") or not org:
        raise AuthorizationError("Company administration access required.")
    rows=api.db.execute(
        "SELECT u.id,u.username,u.display_name,u.status,u.platform_level,m.status AS membership_status "
        "FROM users u JOIN organisation_memberships m ON m.identity_id=u.identity_id "
        "WHERE m.organisation_id=? ORDER BY u.display_name", (org["id"],)
    ).fetchall()
    return {"data":{"items":[dict(r) for r in rows]}}

@router.post("/company/users")
async def company_create_user(request: Request):
    api,user,org=_session_context(request)
    if user["platform_level"] not in ("COMPANY_ADMIN","SYSTEM_ADMIN") or not org:
        raise AuthorizationError("Company administration access required.")
    p=await request.json()
    username=str(p.get("username","")).strip()
    display_name=str(p.get("display_name","")).strip()
    password=str(p.get("password",""))
    if not username or not display_name or len(password)<12:
        raise ValidationError("Username, display name and a password of at least 12 characters are required.")
    created=api.core_service.create_user(username,display_name,password)
    api.core_service.add_membership(created.identity_id,UUID(org["id"]))
    return {"data":{"id":str(created.id),"username":created.username,"display_name":created.display_name,"platform_level":"COMPANY_USER"}}

@router.post("/companies/{organisation_id}/admin")
async def create_company_admin(request: Request, organisation_id: UUID):
    api, user, org = _session_context(request)
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")
    company = api.db.execute("SELECT id FROM organisations WHERE id=? AND status='ACTIVE'", (str(organisation_id),)).fetchone()
    if not company:
        raise ValidationError("Company not found or inactive.")
    p=await request.json()
    username=str(p.get("username","")).strip()
    display_name=str(p.get("display_name","")).strip()
    password=str(p.get("password",""))
    if not username or not display_name or len(password)<12:
        raise ValidationError("Username, display name and a password of at least 12 characters are required.")
    created=api.core_service.create_user(username,display_name,password)
    api.db.execute("UPDATE users SET platform_level='COMPANY_ADMIN' WHERE id=?", (str(created.id),))
    api.db.commit()
    api.core_service.add_membership(created.identity_id,organisation_id)
    return {"data":{"id":str(created.id),"username":created.username,"display_name":created.display_name,"platform_level":"COMPANY_ADMIN","company_id":str(organisation_id)}}






