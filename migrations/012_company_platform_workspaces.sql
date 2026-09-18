-- Company Platform workspace configuration.
-- Module activation/entitlement remains owned by Phoenix System Platform/Core.
CREATE TABLE IF NOT EXISTS company_workspaces (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    visible INTEGER NOT NULL DEFAULT 1 CHECK (visible IN (0,1)),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (organisation_id, module_id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE INDEX IF NOT EXISTS idx_company_workspaces_org_order
    ON company_workspaces(organisation_id, sort_order, display_name);
