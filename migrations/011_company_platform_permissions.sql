-- Company Platform permissions.
-- These permissions govern tenant-level administration only. They do not grant
-- Phoenix platform-control authority such as licensing or module activation.
INSERT OR IGNORE INTO permissions(id, code, name, created_at) VALUES
    ('11111111-1111-4111-8111-000000000001', 'company.activity.view', 'View company activity', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000002', 'company.configuration.manage', 'Manage company configuration', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000003', 'company.memberships.manage', 'Manage company memberships', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000004', 'company.reports.view', 'View company reports', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000005', 'company.roles.manage', 'Manage company roles', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000006', 'company.users.manage', 'Manage company users', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000007', 'company.visibility.manage', 'Manage company data visibility', CURRENT_TIMESTAMP),
    ('11111111-1111-4111-8111-000000000008', 'company.workspaces.manage', 'Manage company workspaces', CURRENT_TIMESTAMP);
