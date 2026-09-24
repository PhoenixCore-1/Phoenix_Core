PRAGMA foreign_keys = ON;

ALTER TABLE production_orders
ADD COLUMN bom_version_id TEXT;

ALTER TABLE production_orders
ADD COLUMN spc_definition_id TEXT;

CREATE INDEX idx_production_orders_bom_version
ON production_orders(bom_version_id);

CREATE INDEX idx_production_orders_spc_definition
ON production_orders(spc_definition_id);

CREATE TABLE production_order_spc_snapshots (
    id TEXT PRIMARY KEY,
    production_order_id INTEGER NOT NULL,
    organisation_id TEXT NOT NULL,
    spc_definition_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,

    UNIQUE(production_order_id),

    FOREIGN KEY (production_order_id)
        REFERENCES production_orders(production_order_id),

    FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    FOREIGN KEY (spc_definition_id)
        REFERENCES production_spc_definitions(id)
);

CREATE TABLE production_order_spc_snapshot_components (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    cost REAL NOT NULL CHECK (cost >= 0),
    currency TEXT NOT NULL,
    sequence INTEGER NOT NULL,

    UNIQUE(snapshot_id, code),
    UNIQUE(snapshot_id, sequence),

    FOREIGN KEY (snapshot_id)
        REFERENCES production_order_spc_snapshots(id)
);

CREATE INDEX idx_production_order_spc_snapshots_order
ON production_order_spc_snapshots(production_order_id);

CREATE INDEX idx_production_order_spc_snapshots_org
ON production_order_spc_snapshots(organisation_id);

CREATE INDEX idx_production_order_spc_snapshot_components_snapshot
ON production_order_spc_snapshot_components(snapshot_id);
