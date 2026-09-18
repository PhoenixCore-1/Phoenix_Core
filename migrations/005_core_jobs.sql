CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    organisation_id TEXT,
    identity_id TEXT,
    payload TEXT,
    status TEXT NOT NULL,
    scheduled_at TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    failed_at TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    idempotency_key TEXT,
    error_code TEXT,
    error_message TEXT,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (identity_id) REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_at
    ON jobs(scheduled_at);

CREATE INDEX IF NOT EXISTS idx_jobs_organisation
    ON jobs(organisation_id);

CREATE INDEX IF NOT EXISTS idx_jobs_idempotency
    ON jobs(organisation_id, idempotency_key);
