PRAGMA foreign_keys = ON;

-- Phoenix Core v1.1.0
-- Production 360
-- Migration 025
-- Add the missing production order -> current stage foreign key.

CREATE TABLE production_orders_new (
    production_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organisation_id TEXT NOT NULL,
    order_number TEXT NOT NULL,
    purpose TEXT NOT NULL,
    product_ref TEXT NOT NULL,
    product_description TEXT,
    quantity_ordered REAL NOT NULL CHECK (quantity_ordered > 0),
    priority TEXT NOT NULL DEFAULT 'Normal',
    status TEXT NOT NULL DEFAULT 'Planned'
        CHECK (
            status IN (
                'Planned',
                'Released to Production',
                'In Production',
                'On Hold',
                'Completed',
                'Cancelled'
            )
        ),
    current_stage_id INTEGER,
    current_location TEXT,
    planned_start_at TEXT,
    planned_finish_at TEXT,
    planned_eta_at TEXT,
    current_eta_at TEXT,
    eta_source TEXT,
    eta_override_reason TEXT,
    eta_updated_at TEXT,
    eta_updated_by TEXT,
    required_date TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    UNIQUE (organisation_id, order_number),

    FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    FOREIGN KEY (created_by)
        REFERENCES identities(id),

    FOREIGN KEY (eta_updated_by)
        REFERENCES identities(id),

    FOREIGN KEY (current_stage_id)
        REFERENCES production_stages(stage_id)
);

INSERT INTO production_orders_new (
    production_order_id,
    organisation_id,
    order_number,
    purpose,
    product_ref,
    product_description,
    quantity_ordered,
    priority,
    status,
    current_stage_id,
    current_location,
    planned_start_at,
    planned_finish_at,
    planned_eta_at,
    current_eta_at,
    eta_source,
    eta_override_reason,
    eta_updated_at,
    eta_updated_by,
    required_date,
    created_by,
    created_at,
    updated_at
)
SELECT
    production_order_id,
    organisation_id,
    order_number,
    purpose,
    product_ref,
    product_description,
    quantity_ordered,
    priority,
    status,
    current_stage_id,
    current_location,
    planned_start_at,
    planned_finish_at,
    planned_eta_at,
    current_eta_at,
    eta_source,
    eta_override_reason,
    eta_updated_at,
    eta_updated_by,
    required_date,
    created_by,
    created_at,
    updated_at
FROM production_orders;

DROP TABLE production_orders;

ALTER TABLE production_orders_new
    RENAME TO production_orders;

CREATE INDEX IF NOT EXISTS idx_production_orders_org
    ON production_orders(organisation_id);

CREATE INDEX IF NOT EXISTS idx_production_orders_status
    ON production_orders(organisation_id, status);

CREATE INDEX IF NOT EXISTS idx_production_orders_current_stage
    ON production_orders(current_stage_id);
