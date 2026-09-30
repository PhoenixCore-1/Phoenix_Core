-- Phoenix Core
-- 036_company_customer_imports.sql
--
-- Customer Master import infrastructure.
-- Customer business ownership remains outside Phoenix Core.
-- These tables store import audit state and temporary external references.

BEGIN;

CREATE TABLE IF NOT EXISTS import_jobs (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    import_type TEXT NOT NULL,
    source_filename TEXT NOT NULL,
    source_system TEXT NOT NULL,
    status TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    validated_at TEXT,
    confirmed_at TEXT,
    completed_at TEXT,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    invalid_rows INTEGER NOT NULL DEFAULT 0,
    warning_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    updated_rows INTEGER NOT NULL DEFAULT 0,
    unchanged_rows INTEGER NOT NULL DEFAULT 0,
    file_hash TEXT,
    error_summary TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (uploaded_by) REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_import_jobs_organisation
    ON import_jobs(organisation_id);

CREATE INDEX IF NOT EXISTS idx_import_jobs_status
    ON import_jobs(organisation_id, status);

CREATE TABLE IF NOT EXISTS import_job_rows (
    id TEXT PRIMARY KEY,
    import_job_id TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    external_id TEXT,
    warehouse_external_id TEXT,
    raw_data_json TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    validation_errors_json TEXT,
    validation_warnings_json TEXT,
    action TEXT,
    FOREIGN KEY (import_job_id) REFERENCES import_jobs(id)
);

CREATE INDEX IF NOT EXISTS idx_import_job_rows_job
    ON import_job_rows(import_job_id);

CREATE INDEX IF NOT EXISTS idx_import_job_rows_external_id
    ON import_job_rows(import_job_id, external_id);

CREATE TABLE IF NOT EXISTS customer_references (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    source_system TEXT NOT NULL,
    external_customer_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL,
    source_record_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    UNIQUE (
        organisation_id,
        source_system,
        external_customer_id
    )
);

CREATE INDEX IF NOT EXISTS idx_customer_references_organisation
    ON customer_references(organisation_id);

CREATE INDEX IF NOT EXISTS idx_customer_references_external
    ON customer_references(
        organisation_id,
        source_system,
        external_customer_id
    );

COMMIT;