-- Company Platform data visibility policies.
-- Core permissions remain the baseline security authority; these policies narrow
-- company data visibility for authorised users.
CREATE TABLE IF NOT EXISTS company_visibility_rules (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('MEMBERSHIP','ROLE')),
    membership_id TEXT,
    role_id TEXT,
    resource_code TEXT NOT NULL,
    visible INTEGER NOT NULL CHECK (visible IN (0,1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((scope_type='MEMBERSHIP' AND membership_id IS NOT NULL AND role_id IS NULL)
        OR (scope_type='ROLE' AND role_id IS NOT NULL AND membership_id IS NULL)),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (membership_id) REFERENCES organisation_memberships(id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    UNIQUE (organisation_id, scope_type, membership_id, role_id, resource_code)
);
CREATE INDEX IF NOT EXISTS idx_company_visibility_org_resource
    ON company_visibility_rules(organisation_id, resource_code);
CREATE INDEX IF NOT EXISTS idx_company_visibility_membership
    ON company_visibility_rules(membership_id, resource_code);
CREATE INDEX IF NOT EXISTS idx_company_visibility_role
    ON company_visibility_rules(role_id, resource_code);
