from uuid import UUID

from fastapi import Request

from phoenix_core.errors import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
)


def _session_context(request: Request):
    api = request.app.state.core_api
    token = request.cookies.get("phoenix_session")

    if not token:
        raise AuthenticationError("Authentication required.")

    sid = api.resolve_session_id(token)

    row = api.db.execute(
        "SELECT u.id, u.identity_id, u.username, u.display_name, "
        "u.status, u.platform_level "
        "FROM users u "
        "JOIN sessions s ON s.identity_id=u.identity_id "
        "WHERE s.id=?",
        (str(sid),),
    ).fetchone()

    if not row:
        raise AuthenticationError("User session is not valid.")

    org = None

    if row["platform_level"] != "SYSTEM_ADMIN":
        org = api.db.execute(
            "SELECT o.id,o.code,o.name,o.status "
            "FROM organisations o "
            "JOIN organisation_memberships m "
            "ON m.organisation_id=o.id "
            "WHERE m.identity_id=? "
            "AND m.status='ACTIVE' "
            "AND o.status='ACTIVE' LIMIT 1",
            (row["identity_id"],),
        ).fetchone()

    return api, row, org


def _require_system_admin(user):
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError(
            "System Platform access required."
        )


def list_system_companies(request: Request):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    rows = api.db.execute(
        "SELECT id,code,name,status,created_at "
        "FROM organisations ORDER BY name"
    ).fetchall()

    return {
        "data": {
            "items": [dict(row) for row in rows]
        }
    }


def get_system_company(
    request: Request,
    organisation_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

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
        "SELECT m.id,m.code,m.name,m.version,"
        "m.status AS module_status,"
        "e.status AS entitlement_status "
        "FROM modules m "
        "LEFT JOIN module_entitlements e "
        "ON e.module_id=m.id "
        "AND e.organisation_id=? "
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
        })

    return {
        "data": {
            "company": dict(company),
            "modules": module_items,
        }
    }


async def create_system_company(request: Request):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    payload = await request.json()

    code = str(payload.get("code", "")).strip().upper()
    name = str(payload.get("name", "")).strip()

    if not code or not name:
        raise ValidationError(
            "Company code and name are required."
        )

    company = api.system_company_service.create_company(code, name)

    registration_fields = {
        "legal_name": str(
            payload.get("legal_name", "")
        ).strip() or None,
        "trading_name": str(
            payload.get("trading_name", "")
        ).strip() or None,
        "registration_number": str(
            payload.get("registration_number", "")
        ).strip() or None,
        "tax_number": str(
            payload.get("tax_number", "")
        ).strip() or None,
        "primary_email": str(
            payload.get("primary_email", "")
        ).strip() or None,
        "telephone": str(
            payload.get("telephone", "")
        ).strip() or None,
        "website": str(
            payload.get("website", "")
        ).strip() or None,
        "address_line_1": str(
            payload.get("address_line_1", "")
        ).strip() or None,
        "address_line_2": str(
            payload.get("address_line_2", "")
        ).strip() or None,
        "city": str(
            payload.get("city", "")
        ).strip() or None,
        "province": str(
            payload.get("province", "")
        ).strip() or None,
        "postal_code": str(
            payload.get("postal_code", "")
        ).strip() or None,
        "country": str(
            payload.get("country", "")
        ).strip() or None,
        "industry": str(
            payload.get("industry", "")
        ).strip() or None,
        "company_type": str(
            payload.get("company_type", "")
        ).strip() or None,
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
            "id": str(company.id),
            "code": company.code,
            "name": company.name,
            "status": company.status,
            **registration_fields,
        }
    }

def suspend_system_company(
    request: Request,
    organisation_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    company = api.db.execute(
        "SELECT id FROM organisations WHERE id=?",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found.")

    updated = api.system_company_service.suspend_company(organisation_id)

    return {
        "data": {
            "id": str(updated.id),
            "status": updated.status,
        }
    }


def activate_system_company(
    request: Request,
    organisation_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    company = api.db.execute(
        "SELECT id FROM organisations WHERE id=?",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found.")

    updated = api.system_company_service.activate_company(organisation_id)

    return {
        "data": {
            "id": str(updated.id),
            "status": updated.status,
        }
    }

def activate_system_company_module(
    request: Request,
    organisation_id: UUID,
    module_code: str,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    module = api.db.execute(
        "SELECT id,code,name,version,status "
        "FROM modules WHERE code=?",
        (module_code,),
    ).fetchone()

    if not module:
        raise ValidationError("Module not found.")

    company = api.db.execute(
        "SELECT id FROM organisations "
        "WHERE id=? AND status='ACTIVE'",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found or inactive.")

    module_id = UUID(module["id"])

    try:
        entitlement = api.entitlement_service.get_for_organisation_module(
            organisation_id,
            module_id,
        )
    except Exception:
        entitlement = None

    if entitlement:
        if entitlement.status == "ACTIVE":
            raise ValidationError(
                "Organisation is already entitled to this module."
            )

        entitlement = api.entitlement_service.activate(
            entitlement.id
        )
    else:
        entitlement = api.entitlement_service.grant(
            organisation_id,
            module_id,
        )

    return {
        "data": {
            "company_id": str(organisation_id),
            "module_code": module_code,
            "entitlement_id": str(entitlement.id),
            "status": entitlement.status,
        }
    }


def suspend_system_company_module(
    request: Request,
    organisation_id: UUID,
    module_code: str,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    module = api.db.execute(
        "SELECT id FROM modules WHERE code=?",
        (module_code,),
    ).fetchone()

    if not module:
        raise ValidationError("Module not found.")

    try:
        entitlement = api.entitlement_service.get_for_organisation_module(
            organisation_id,
            UUID(module["id"]),
        )
    except Exception:
        entitlement = None

    if not entitlement:
        raise ValidationError(
            "Module is not activated for this company."
        )

    updated = api.entitlement_service.suspend(
        entitlement.id
    )

    return {
        "data": {
            "company_id": str(organisation_id),
            "module_code": module_code,
            "entitlement_id": str(updated.id),
            "status": updated.status,
        }
    }
from uuid import UUID
from fastapi import Request
from phoenix_core.errors import AuthorizationError, ValidationError

async def create_system_company_admin(request: Request, organisation_id: UUID):
    api, user, org = _session_context(request)

    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")

    company = api.db.execute(
        "SELECT id FROM organisations WHERE id=? AND status='ACTIVE'",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found or inactive.")

    p = await request.json()
    username = str(p.get("username", "")).strip()
    display_name = str(p.get("display_name", "")).strip()
    password = str(p.get("password", ""))

    if not username or not display_name or len(password) < 12:
        raise ValidationError(
            "Username, display name and a password of at least 12 characters are required."
        )

    created = api.user_service.create_user(username=username, display_name=display_name, password=password)

    api.db.execute(
        "UPDATE users SET platform_level='COMPANY_ADMIN' WHERE id=?",
        (str(created.id),),
    )
    api.db.commit()

    api.company_membership_service.add_membership(
        created.identity_id,
        organisation_id,
    )

    membership = api.db.execute(
        """
        SELECT id
        FROM organisation_memberships
        WHERE identity_id=?
          AND organisation_id=?
          AND status='ACTIVE'
        """,
        (
            str(created.identity_id),
            str(organisation_id),
        ),
    ).fetchone()

    if not membership:
        raise ValidationError(
            "Company Admin membership could not be established."
        )

    role = api.db.execute(
        """
        SELECT id
        FROM roles
        WHERE organisation_id=?
          AND code='COMPANY.ADMIN'
          AND scope='ORGANISATION'
          AND status='ACTIVE'
        """,
        (str(organisation_id),),
    ).fetchone()

    if not role:
        raise ValidationError(
            "Protected COMPANY.ADMIN role is not configured for this company."
        )

    api.role_service.assign_protected_company_admin(
        UUID(str(membership["id"])),
        UUID(str(role["id"])),
    )

    return {
        "data": {
            "id": str(created.id),
            "username": created.username,
            "display_name": created.display_name,
            "platform_level": "COMPANY_ADMIN",
            "company_id": str(organisation_id),
        }
    }




def get_system_company_admin_access(
    request: Request,
    organisation_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    company = api.db.execute(
        """
        SELECT id, code, name, status
        FROM organisations
        WHERE id=? AND status='ACTIVE'
        """,
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError(
            "Company not found or inactive."
        )

    admin = api.db.execute(
        """
        SELECT
            u.id,
            u.identity_id,
            u.username,
            u.display_name,
            u.status,
            u.platform_level,
            u.password_reset_required,
            m.id AS membership_id,
            m.status AS membership_status
        FROM users u
        JOIN organisation_memberships m
          ON m.identity_id=u.identity_id
        WHERE m.organisation_id=?
          AND m.status='ACTIVE'
          AND u.platform_level='COMPANY_ADMIN'
        ORDER BY u.created_at
        LIMIT 1
        """,
        (str(organisation_id),),
    ).fetchone()

    if not admin:
        return {
            "data": {
                "company": dict(company),
                "admin": None,
                "role": None,
                "permissions": [],
            }
        }

    role = api.db.execute(
        """
        SELECT
            r.id,
            r.code,
            r.name,
            r.scope,
            r.status
        FROM role_assignments ra
        JOIN roles r
          ON r.id=ra.role_id
        WHERE ra.membership_id=?
          AND r.status='ACTIVE'
        ORDER BY r.code
        LIMIT 1
        """,
        (str(admin["membership_id"]),),
    ).fetchone()

    permissions = []

    if role:
        permission_rows = api.db.execute(
            """
            SELECT
                p.id,
                p.code,
                p.name
            FROM role_permissions rp
            JOIN permissions p
              ON p.id=rp.permission_id
            WHERE rp.role_id=?
            ORDER BY p.code
            """,
            (str(role["id"]),),
        ).fetchall()

        permissions = [dict(row) for row in permission_rows]

    return {
        "data": {
            "company": dict(company),
            "admin": dict(admin),
            "role": dict(role) if role else None,
            "permissions": permissions,
        }
    }

def get_system_company_admin(
    request: Request,
    organisation_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    company = api.db.execute(
        "SELECT id,code,name,status "
        "FROM organisations "
        "WHERE id=? AND status='ACTIVE'",
        (str(organisation_id),),
    ).fetchone()

    if not company:
        raise ValidationError("Company not found or inactive.")

    admin = api.db.execute(
        """
        SELECT
            u.id,
            u.identity_id,
            u.username,
            u.display_name,
            u.status,
            u.platform_level,
            u.password_reset_required,
            u.created_at,
            m.id AS membership_id,
            m.status AS membership_status
        FROM users u
        JOIN organisation_memberships m
            ON m.identity_id=u.identity_id
        WHERE m.organisation_id=?
          AND m.status='ACTIVE'
          AND u.platform_level='COMPANY_ADMIN'
        ORDER BY u.created_at
        LIMIT 1
        """,
        (str(organisation_id),),
    ).fetchone()

    if not admin:
        return {
            "data": {
                "company": dict(company),
                "admin": None,
            }
        }

    return {
        "data": {
            "company": dict(company),
            "admin": dict(admin),
        }
    }


