PRAGMA foreign_keys = ON;

CREATE TABLE production_bom_versions_new (
    id TEXT PRIMARY KEY,
    bom_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PUBLISHED','RETIRED')),
    created_at TEXT NOT NULL,
    published_at TEXT,
    created_by TEXT,
    published_by TEXT,
    spc_definition_id TEXT,

    UNIQUE(bom_id, version_number),

    FOREIGN KEY (bom_id)
        REFERENCES production_boms(id),

    FOREIGN KEY (created_by)
        REFERENCES identities(id),

    FOREIGN KEY (published_by)
        REFERENCES identities(id),

    FOREIGN KEY (spc_definition_id)
        REFERENCES production_spc_definitions(id)
);

INSERT INTO production_bom_versions_new (
    id, bom_id, version_number, status,
    created_at, published_at,
    created_by, published_by,
    spc_definition_id
)
SELECT
    id, bom_id, version_number, status,
    created_at, published_at,
    created_by, published_by,
    spc_definition_id
FROM production_bom_versions;

DROP TABLE production_bom_versions;

ALTER TABLE production_bom_versions_new
RENAME TO production_bom_versions;

CREATE INDEX idx_production_bom_versions_spc_definition
ON production_bom_versions(spc_definition_id);
