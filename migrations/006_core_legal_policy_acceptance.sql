PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS policies (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    policy_code TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('DRAFT','ACTIVE','RETIRED')
    ),
    required_acceptance INTEGER NOT NULL DEFAULT 0 CHECK (
        required_acceptance IN (0,1)
    ),
    applicable_scope TEXT NOT NULL CHECK (
        applicable_scope IN ('PLATFORM','ORGANISATION')
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(organisation_id, policy_code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE INDEX IF NOT EXISTS idx_policies_org_status
ON policies(organisation_id, status);

CREATE TABLE IF NOT EXISTS policy_versions (
    id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    version_label TEXT NOT NULL,
    document_id TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    acceptance_required INTEGER NOT NULL CHECK (
        acceptance_required IN (0,1)
    ),
    status TEXT NOT NULL CHECK (
        status IN ('DRAFT','ACTIVE','RETIRED')
    ),
    created_at TEXT NOT NULL,
    UNIQUE(policy_id, version_number),
    FOREIGN KEY (policy_id) REFERENCES policies(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_policy_versions_policy_status
ON policy_versions(policy_id, status);

CREATE INDEX IF NOT EXISTS idx_policy_versions_effective
ON policy_versions(effective_at);

CREATE TABLE IF NOT EXISTS policy_acceptances (
    id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    policy_version_id TEXT NOT NULL,
    organisation_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    session_id TEXT,
    request_id TEXT,
    accepted_at TEXT NOT NULL,
    audit_event_id TEXT,
    FOREIGN KEY (policy_id) REFERENCES policies(id),
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (identity_id) REFERENCES identities(id),
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (audit_event_id) REFERENCES audit_events(id)
);

CREATE INDEX IF NOT EXISTS idx_policy_acceptances_org
ON policy_acceptances(organisation_id);

CREATE INDEX IF NOT EXISTS idx_policy_acceptances_identity
ON policy_acceptances(organisation_id, identity_id);

CREATE INDEX IF NOT EXISTS idx_policy_acceptances_version
ON policy_acceptances(policy_version_id);

CREATE INDEX IF NOT EXISTS idx_policy_acceptances_request
ON policy_acceptances(request_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_policy_acceptance_identity_version
ON policy_acceptances(
    organisation_id,
    identity_id,
    policy_version_id
);
