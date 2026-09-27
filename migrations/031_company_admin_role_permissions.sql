-- Phoenix Core
-- 031_company_admin_role_permissions.sql
--
-- Repair migration: ensure the protected COMPANY.ADMIN role
-- has the complete company administration permission set.

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
WHERE r.code = 'COMPANY.ADMIN'
  AND r.scope = 'ORGANISATION';
