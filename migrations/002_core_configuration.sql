PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS core_settings (
    id TEXT PRIMARY KEY,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('GLOBAL','ORGANISATION')),
    organisation_id TEXT,
    key TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (value_type IN ('STRING','INTEGER','NUMBER','BOOLEAN','JSON')),
    value TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(scope_type, organisation_id, key),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS feature_flags (
    id TEXT PRIMARY KEY,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('GLOBAL','ORGANISATION')),
    organisation_id TEXT,
    key TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK (enabled IN (0,1)),
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(scope_type, organisation_id, key),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE INDEX IF NOT EXISTS idx_core_settings_org ON core_settings(organisation_id, key);
CREATE INDEX IF NOT EXISTS idx_feature_flags_org ON feature_flags(organisation_id, key);
