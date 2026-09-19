CREATE TABLE IF NOT EXISTS legal_requirements (
    id TEXT PRIMARY KEY,
    requirement_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,

    document_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL,

    action_type TEXT NOT NULL
        CHECK (action_type IN ('ACCEPT', 'SIGN', 'ACKNOWLEDGE', 'CONSENT')),

    scope TEXT NOT NULL
        CHECK (scope IN ('COMPANY', 'USER')),

    enforcement TEXT NOT NULL DEFAULT 'NOTICE_ONLY'
        CHECK (
            enforcement IN (
                'NOTICE_ONLY',
                'REQUIRE_ACTION',
                'RESTRICT_FEATURE',
                'SUSPEND_SERVICE'
            )
        ),

    jurisdiction TEXT,
    required INTEGER NOT NULL DEFAULT 1
        CHECK (required IN (0, 1)),

    effective_from TEXT,
    due_at TEXT,

    status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'ACTIVE', 'RETIRED', 'SUPERSEDED')),

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (document_id)
        REFERENCES documents(id),

    FOREIGN KEY (document_version_id)
        REFERENCES document_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_legal_requirements_status
    ON legal_requirements(status);

CREATE INDEX IF NOT EXISTS idx_legal_requirements_document
    ON legal_requirements(document_id, document_version_id);

CREATE INDEX IF NOT EXISTS idx_legal_requirements_scope
    ON legal_requirements(scope, status);


CREATE TABLE IF NOT EXISTS legal_requirement_assignments (
    id TEXT PRIMARY KEY,

    requirement_id TEXT NOT NULL,
    organisation_id TEXT NOT NULL,
    identity_id TEXT,

    assignment_scope TEXT NOT NULL
        CHECK (assignment_scope IN ('COMPANY', 'USER')),

    status TEXT NOT NULL DEFAULT 'ASSIGNED'
        CHECK (
            status IN (
                'ASSIGNED',
                'COMPLETED',
                'DECLINED',
                'SUPERSEDED',
                'CANCELLED'
            )
        ),

    assigned_at TEXT NOT NULL,
    due_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (requirement_id)
        REFERENCES legal_requirements(id),

    FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    FOREIGN KEY (identity_id)
        REFERENCES identities(id),

    CHECK (
        (assignment_scope = 'COMPANY' AND identity_id IS NULL)
        OR
        (assignment_scope = 'USER' AND identity_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_legal_assignments_requirement
    ON legal_requirement_assignments(requirement_id);

CREATE INDEX IF NOT EXISTS idx_legal_assignments_organisation
    ON legal_requirement_assignments(organisation_id, status);

CREATE INDEX IF NOT EXISTS idx_legal_assignments_identity
    ON legal_requirement_assignments(identity_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_company_assignment
    ON legal_requirement_assignments(requirement_id, organisation_id)
    WHERE assignment_scope = 'COMPANY';

CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_user_assignment
    ON legal_requirement_assignments(requirement_id, organisation_id, identity_id)
    WHERE assignment_scope = 'USER';


CREATE TABLE IF NOT EXISTS legal_acceptance_evidence (
    id TEXT PRIMARY KEY,

    requirement_id TEXT NOT NULL,
    assignment_id TEXT NOT NULL,

    organisation_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,

    document_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL,
    document_checksum TEXT NOT NULL,

    action_type TEXT NOT NULL
        CHECK (action_type IN ('ACCEPT', 'SIGN', 'ACKNOWLEDGE', 'CONSENT')),

    completed_at TEXT NOT NULL,

    confirmation_reference TEXT,
    signature_provider TEXT,
    signature_reference TEXT,
    technical_evidence TEXT,

    audit_event_id TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (requirement_id)
        REFERENCES legal_requirements(id),

    FOREIGN KEY (assignment_id)
        REFERENCES legal_requirement_assignments(id),

    FOREIGN KEY (organisation_id)
        REFERENCES organisations(id),

    FOREIGN KEY (identity_id)
        REFERENCES identities(id),

    FOREIGN KEY (document_id)
        REFERENCES documents(id),

    FOREIGN KEY (document_version_id)
        REFERENCES document_versions(id)
);

CREATE INDEX IF NOT EXISTS idx_legal_evidence_requirement
    ON legal_acceptance_evidence(requirement_id);

CREATE INDEX IF NOT EXISTS idx_legal_evidence_assignment
    ON legal_acceptance_evidence(assignment_id);

CREATE INDEX IF NOT EXISTS idx_legal_evidence_identity
    ON legal_acceptance_evidence(identity_id, organisation_id);

CREATE INDEX IF NOT EXISTS idx_legal_evidence_document
    ON legal_acceptance_evidence(document_id, document_version_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_legal_evidence_assignment
    ON legal_acceptance_evidence(assignment_id);
