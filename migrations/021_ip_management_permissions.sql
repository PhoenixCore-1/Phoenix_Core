-- Migration 021: IP Management Permissions

INSERT OR IGNORE INTO permissions(id, code, name, created_at) VALUES
(
    '11111111-1111-4111-8111-000000000021',
    'system.ip_management.view',
    'View IP management',
    CURRENT_TIMESTAMP
),
(
    '11111111-1111-4111-8111-000000000022',
    'system.ip_management.manage',
    'Manage IP ownership',
    CURRENT_TIMESTAMP
);
