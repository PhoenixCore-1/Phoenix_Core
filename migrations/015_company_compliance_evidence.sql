-- Company Platform evidence records are tenant-scoped references to authoritative
-- Core documents/legal records. They are not a second document or legal authority.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS company_compliance_evidence (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    policy_version_id TEXT,
    document_id TEXT,
    document_version_id TEXT,
    evidence_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','EXPIRED','ARCHIVED')),
    valid_from TEXT,
    valid_until TEXT,
    created_by_identity_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (policy_version_id) REFERENCES policy_versions(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id),
    FOREIGN KEY (created_by_identity_id) REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_company_evidence_org
    ON company_compliance_evidence(organisation_id, status);
CREATE INDEX IF NOT EXISTS idx_company_evidence_policy_version
    ON company_compliance_evidence(organisation_id, policy_version_id);
CREATE INDEX IF NOT EXISTS idx_company_evidence_document
    ON company_compliance_evidence(organisation_id, document_id);
CREATE INDEX IF NOT EXISTS idx_company_evidence_expiry
    ON company_compliance_evidence(organisation_id, valid_until);
