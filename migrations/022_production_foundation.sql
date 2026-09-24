-- Phoenix Core v1.1.0
-- Production 360 foundation
-- Migration 022
--
-- Ownership:
--   Phoenix Core organisations.id is the authoritative tenant/company boundary.
--   Production does not create a parallel company/tenant model.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS production_products (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    uom TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(organisation_id, code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (created_by) REFERENCES identities(id),
    FOREIGN KEY (updated_by) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS production_boms (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(organisation_id, code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (product_id) REFERENCES production_products(id),
    FOREIGN KEY (created_by) REFERENCES identities(id),
    FOREIGN KEY (updated_by) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS production_bom_versions (
    id TEXT PRIMARY KEY,
    bom_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PUBLISHED','RETIRED')),
    created_at TEXT NOT NULL,
    published_at TEXT,
    created_by TEXT,
    published_by TEXT,
    UNIQUE(bom_id, version_number),
    FOREIGN KEY (bom_id) REFERENCES production_boms(id),
    FOREIGN KEY (created_by) REFERENCES identities(id),
    FOREIGN KEY (published_by) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS production_bom_components (
    id TEXT PRIMARY KEY,
    bom_version_id TEXT NOT NULL,
    component_product_id TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),
    uom TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (bom_version_id) REFERENCES production_bom_versions(id),
    FOREIGN KEY (component_product_id) REFERENCES production_products(id),
    UNIQUE(bom_version_id, sequence)
);

CREATE TABLE IF NOT EXISTS production_spc_definitions (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    updated_by TEXT,
    UNIQUE(organisation_id, code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (created_by) REFERENCES identities(id),
    FOREIGN KEY (updated_by) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS production_spc_cost_components (
    id TEXT PRIMARY KEY,
    spc_definition_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    cost REAL NOT NULL CHECK (cost >= 0),
    currency TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (spc_definition_id) REFERENCES production_spc_definitions(id),
    UNIQUE(spc_definition_id, code),
    UNIQUE(spc_definition_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_production_products_org
    ON production_products(organisation_id);

CREATE INDEX IF NOT EXISTS idx_production_boms_org
    ON production_boms(organisation_id);

CREATE INDEX IF NOT EXISTS idx_production_boms_product
    ON production_boms(product_id);

CREATE INDEX IF NOT EXISTS idx_production_bom_versions_bom
    ON production_bom_versions(bom_id);

CREATE INDEX IF NOT EXISTS idx_production_bom_components_version
    ON production_bom_components(bom_version_id);

CREATE INDEX IF NOT EXISTS idx_production_spc_org
    ON production_spc_definitions(organisation_id);

CREATE INDEX IF NOT EXISTS idx_production_spc_cost_components_definition
    ON production_spc_cost_components(spc_definition_id);
