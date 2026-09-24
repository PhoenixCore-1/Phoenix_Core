-- Phoenix Core v1.1.0
-- Production 360 permissions
-- Migration 023

INSERT OR IGNORE INTO permissions(id, code, name, created_at) VALUES
    ('22222222-2222-4222-8222-000000000001', 'production.view', 'View Production 360', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000002', 'production.order.create', 'Create manufacturing orders', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000003', 'production.order.edit', 'Edit manufacturing orders', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000004', 'production.order.release', 'Release manufacturing orders', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000005', 'production.order.execute', 'Execute manufacturing orders', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000006', 'production.quantity.record', 'Record production quantities', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000007', 'production.quantity.adjust', 'Adjust production quantities', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000008', 'production.bom.view', 'View production BOMs', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000009', 'production.bom.manage', 'Manage production BOMs', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000010', 'production.spc.view', 'View production SPC definitions', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000011', 'production.spc.manage', 'Manage production SPC definitions', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000012', 'production.eta.view', 'View production ETA', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000013', 'production.eta.recalculate', 'Recalculate production ETA', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000014', 'production.ai.use', 'Use Production AI assistance', CURRENT_TIMESTAMP),
    ('22222222-2222-4222-8222-000000000015', 'production.admin', 'Administer Production 360', CURRENT_TIMESTAMP);
