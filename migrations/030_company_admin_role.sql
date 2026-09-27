-- Phoenix Core
-- 030_company_admin_role.sql
--
-- Establish the protected company administrator role for every
-- organisation that already exists.
--
-- The role is protected by the Core RoleService using the reserved
-- role code COMPANY.ADMIN.

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

-- Company administration permissions.
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
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
WHERE r.code = 'COMPANY.ADMIN';

