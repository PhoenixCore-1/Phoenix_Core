CREATE TABLE production_spc_definitions_new (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','ACTIVE','RETIRED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(organisation_id, code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (created_by) REFERENCES identities(id),
    FOREIGN KEY (updated_by) REFERENCES identities(id)
);

INSERT INTO production_spc_definitions_new (
    id, organisation_id, code, name, status,
    created_at, updated_at, created_by, updated_by
)
SELECT
    id, organisation_id, code, name,
    CASE WHEN status = 'INACTIVE' THEN 'RETIRED' ELSE status END,
    created_at, updated_at, created_by, updated_by
FROM production_spc_definitions;

DROP TABLE production_spc_definitions;

ALTER TABLE production_spc_definitions_new
RENAME TO production_spc_definitions;

CREATE INDEX IF NOT EXISTS idx_production_spc_definitions_org
ON production_spc_definitions(organisation_id);
