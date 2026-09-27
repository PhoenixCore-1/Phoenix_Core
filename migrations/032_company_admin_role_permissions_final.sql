-- Phoenix Core
-- 032_company_admin_role_permissions_final.sql
--
-- Ensure protected COMPANY.ADMIN roles have their required
-- company administration permissions.

BEGIN;

INSERT OR IGNORE INTO role_permissions (role_id, permission_id, created_at)
SELECT
    r.id,
    p.id,
    datetime('now')
FROM roles r
JOIN permissions p
    ON p.code IN (
        'company.activity.view',
        'company.configuration.manage',
        'company.memberships.manage',
        'company.reports.view',
        'company.roles.manage',
        'company.users.manage',
        'company.visibility.manage',
        'company.workspaces.manage'
    )
WHERE r.code = 'COMPANY.ADMIN'
  AND r.scope = 'ORGANISATION';

COMMIT;
