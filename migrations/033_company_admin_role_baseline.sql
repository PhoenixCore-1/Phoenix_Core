-- Phoenix Core
-- 033_company_admin_role_baseline.sql
--
-- Establish the least-privilege protected COMPANY.ADMIN baseline
-- and repair existing Company Admin memberships.

BEGIN;

-- 1. Add the company data-import capability.
INSERT OR IGNORE INTO permissions (
    id,
    code,
    name,
    created_at
)
VALUES (
    lower(hex(randomblob(16))),
    'company.data.import',
    'Import Company Data',
    datetime('now')
);

-- 2. Ensure every active organisation has the protected role.
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
    'COMPANY.ADMIN',
    'Company Administrator',
    'ORGANISATION',
    'ACTIVE',
    datetime('now')
FROM organisations o
WHERE o.status = 'ACTIVE';

-- 3. Remove the legacy broad COMPANY.ADMIN permissions only.
DELETE FROM role_permissions
WHERE role_id IN (
    SELECT id
    FROM roles
    WHERE code = 'COMPANY.ADMIN'
      AND scope = 'ORGANISATION'
)
AND permission_id IN (
    SELECT id
    FROM permissions
    WHERE code IN (
        'company.activity.view',
        'company.configuration.manage',
        'company.memberships.manage',
        'company.reports.view',
        'company.roles.manage',
        'company.users.manage',
        'company.visibility.manage',
        'company.workspaces.manage'
    )
);

-- 4. Establish the least-privilege COMPANY.ADMIN baseline.
INSERT OR IGNORE INTO role_permissions (
    role_id,
    permission_id,
    created_at
)
SELECT
    r.id,
    p.id,
    datetime('now')
FROM roles r
JOIN permissions p
    ON p.code IN (
        'company.users.manage',
        'company.memberships.manage',
        'company.roles.manage',
        'company.data.import'
    )
WHERE r.code = 'COMPANY.ADMIN'
  AND r.scope = 'ORGANISATION'
  AND r.status = 'ACTIVE';

-- 5. Assign COMPANY.ADMIN to every active Company Admin membership.
INSERT OR IGNORE INTO role_assignments (
    id,
    membership_id,
    role_id,
    created_at
)
SELECT
    lower(hex(randomblob(16))),
    m.id,
    r.id,
    datetime('now')
FROM organisation_memberships m
JOIN users u
    ON u.identity_id = m.identity_id
JOIN roles r
    ON r.organisation_id = m.organisation_id
   AND r.code = 'COMPANY.ADMIN'
   AND r.scope = 'ORGANISATION'
   AND r.status = 'ACTIVE'
JOIN organisations o
    ON o.id = m.organisation_id
WHERE m.status = 'ACTIVE'
  AND o.status = 'ACTIVE'
  AND u.platform_level = 'COMPANY_ADMIN';

COMMIT;

