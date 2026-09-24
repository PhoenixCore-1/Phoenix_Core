PRAGMA foreign_keys = ON;

-- ============================================================
-- Production 360 execution foundation
-- Migration 024
--
-- Core remains the owner of these persistence tables.
-- Production owns the business rules executed against them.
-- ============================================================

CREATE TABLE IF NOT EXISTS production_orders (
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

    CONSTRAINT uq_production_orders_org_number
        UNIQUE (organisation_id, order_number),

    CONSTRAINT fk_production_orders_org
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    CONSTRAINT fk_production_orders_created_by
        FOREIGN KEY (created_by)
        REFERENCES identities(id),

    CONSTRAINT fk_production_orders_eta_updated_by
        FOREIGN KEY (eta_updated_by)
        REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_production_orders_org
    ON production_orders(organisation_id);

CREATE INDEX IF NOT EXISTS idx_production_orders_status
    ON production_orders(organisation_id, status);

CREATE TABLE IF NOT EXISTS production_stages (
    stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_order_id INTEGER NOT NULL,
    stage_code TEXT NOT NULL,
    stage_name TEXT NOT NULL,
    stage_sequence INTEGER NOT NULL CHECK (stage_sequence > 0),
    location TEXT,
    status TEXT NOT NULL DEFAULT 'Ready'
        CHECK (
            status IN (
                'Ready',
                'In Progress',
                'On Hold',
                'Complete',
                'Waiting'
            )
        ),
    start_datetime TEXT,
    finish_datetime TEXT,
    quantity_completed REAL NOT NULL DEFAULT 0,
    quantity_rejected REAL NOT NULL DEFAULT 0,
    notes TEXT,

    CONSTRAINT uq_production_stage_sequence
        UNIQUE (production_order_id, stage_sequence),

    CONSTRAINT uq_production_stage_code
        UNIQUE (production_order_id, stage_code),

    CONSTRAINT fk_production_stages_order
        FOREIGN KEY (production_order_id)
        REFERENCES production_orders(production_order_id)
);

CREATE INDEX IF NOT EXISTS idx_production_stages_order
    ON production_stages(production_order_id, stage_sequence);

CREATE TABLE IF NOT EXISTS production_quantity_ledger (
    quantity_ledger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organisation_id TEXT NOT NULL,
    production_order_id INTEGER NOT NULL,
    stage_id INTEGER,
    quantity_type TEXT NOT NULL
        CHECK (
            quantity_type IN (
                'ACCEPTED',
                'REJECTED',
                'REWORK'
            )
        ),
    quantity REAL NOT NULL CHECK (quantity >= 0),
    uom_code TEXT NOT NULL,
    reason_code TEXT,
    notes TEXT,
    recorded_by TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    idempotency_key TEXT,

    CONSTRAINT fk_quantity_ledger_org
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    CONSTRAINT fk_quantity_ledger_order
        FOREIGN KEY (production_order_id)
        REFERENCES production_orders(production_order_id),

    CONSTRAINT fk_quantity_ledger_stage
        FOREIGN KEY (stage_id)
        REFERENCES production_stages(stage_id),

    CONSTRAINT fk_quantity_ledger_recorded_by
        FOREIGN KEY (recorded_by)
        REFERENCES identities(id),

    CONSTRAINT uq_quantity_ledger_idempotency
        UNIQUE (organisation_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_quantity_ledger_order
    ON production_quantity_ledger(
        organisation_id,
        production_order_id
    );

CREATE INDEX IF NOT EXISTS idx_quantity_ledger_stage
    ON production_quantity_ledger(
        organisation_id,
        production_order_id,
        stage_id
    );

CREATE TABLE IF NOT EXISTS production_events (
    production_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organisation_id TEXT NOT NULL,
    production_order_id INTEGER NOT NULL,
    stage_id INTEGER,
    event_type TEXT NOT NULL,
    user_id TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,

    CONSTRAINT fk_production_events_org
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    CONSTRAINT fk_production_events_order
        FOREIGN KEY (production_order_id)
        REFERENCES production_orders(production_order_id),

    CONSTRAINT fk_production_events_stage
        FOREIGN KEY (stage_id)
        REFERENCES production_stages(stage_id),

    CONSTRAINT fk_production_events_user
        FOREIGN KEY (user_id)
        REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_production_events_order
    ON production_events(
        organisation_id,
        production_order_id,
        created_at
    );

CREATE TABLE IF NOT EXISTS production_holds (
    hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
    organisation_id TEXT NOT NULL,
    production_order_id INTEGER NOT NULL,
    stage_id INTEGER,
    problem_type TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_quantity REAL NOT NULL DEFAULT 0
        CHECK (affected_quantity >= 0),
    reported_by TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open'
        CHECK (status IN ('Open', 'Resolved')),
    resolution TEXT,
    resolved_at TEXT,
    resolved_by TEXT,
    eta_impact_minutes INTEGER,
    eta_recalculated_at TEXT,

    CONSTRAINT fk_production_holds_org
        FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    CONSTRAINT fk_production_holds_order
        FOREIGN KEY (production_order_id)
        REFERENCES production_orders(production_order_id),

    CONSTRAINT fk_production_holds_stage
        FOREIGN KEY (stage_id)
        REFERENCES production_stages(stage_id),

    CONSTRAINT fk_production_holds_reported_by
        FOREIGN KEY (reported_by)
        REFERENCES identities(id),

    CONSTRAINT fk_production_holds_resolved_by
        FOREIGN KEY (resolved_by)
        REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_production_holds_order
    ON production_holds(
        organisation_id,
        production_order_id,
        status
    );

-- Add the order -> current-stage FK after both tables exist.
-- SQLite requires the referenced stage table to exist, which it now does.
CREATE INDEX IF NOT EXISTS idx_production_orders_current_stage
    ON production_orders(current_stage_id);
