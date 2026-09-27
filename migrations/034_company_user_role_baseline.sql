-- Phoenix Core
-- 034_company_user_role_baseline.sql
--
-- Establish the baseline COMPANY.USER role.
-- COMPANY.USER intentionally carries no permissions by default.
-- Additional permissions/roles can be assigned as module access is defined.

BEGIN;

INSERT OR IGNORE INTO roles (
    id,
    organisation_id,
    code,
    name,
    scope,
    status,
    created_at
)
SELECT
    lower(hex(randomblob(16))),
    o.id,
    'COMPANY.USER',
    'Company User',
    'ORGANISATION',
    'ACTIVE',
    datetime('now')
FROM organisations o
WHERE o.status = 'ACTIVE';

COMMIT;
