-- Migration 019: Phoenix Intellectual Property & Ownership Foundation
--
-- Establishes ownership and licensing records for Phoenix platform IP,
-- customer-owned data/content, third-party IP and future legal-entity ownership.
--
-- Existing Documents and Audit subsystems remain authoritative for evidence.

CREATE TABLE IF NOT EXISTS ip_owners (
    id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL CHECK (
        owner_type IN (
            'FOUNDER',
            'LEGAL_ENTITY',
            'COMPANY',
            'THIRD_PARTY',
            'OPEN_SOURCE'
        )
    ),
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ip_assets (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    asset_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    asset_type TEXT NOT NULL CHECK (
        asset_type IN (
            'SOFTWARE',
            'ARCHITECTURE',
            'DATABASE',
            'ALGORITHM',
            'DESIGN',
            'DOCUMENTATION',
            'BRAND',
            'TRADEMARK',
            'INVENTION',
            'TRADE_SECRET',
            'CUSTOMER_CONTENT',
            'CUSTOMER_DATA',
            'THIRD_PARTY'
        )
    ),
    confidentiality_class TEXT NOT NULL DEFAULT 'INTERNAL'
        CHECK (
            confidentiality_class IN (
                'PUBLIC',
                'INTERNAL',
                'CONFIDENTIAL',
                'RESTRICTED',
                'TRADE_SECRET'
            )
        ),
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('DRAFT','ACTIVE','RETIRED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES ip_owners(id)
);

CREATE TABLE IF NOT EXISTS ip_asset_versions (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    version_label TEXT NOT NULL,
    description TEXT,
    document_id TEXT,
    document_version_id TEXT,
    checksum TEXT,
    effective_from TEXT,
    retired_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_ip_asset_versions
    ON ip_asset_versions(asset_id, version_label);

CREATE TABLE IF NOT EXISTS ip_ownership_events (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    previous_owner_id TEXT,
    new_owner_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'CREATED',
            'ASSIGNED',
            'TRANSFERRED',
            'RETURNED',
            'RECLASSIFIED'
        )
    ),
    reason TEXT,
    document_id TEXT,
    document_version_id TEXT,
    effective_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by_identity_id TEXT,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (previous_owner_id) REFERENCES ip_owners(id),
    FOREIGN KEY (new_owner_id) REFERENCES ip_owners(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE INDEX IF NOT EXISTS ix_ip_ownership_events_asset
    ON ip_ownership_events(asset_id, effective_at);

CREATE TABLE IF NOT EXISTS ip_licences (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    licence_type TEXT NOT NULL CHECK (
        licence_type IN (
            'PROPRIETARY',
            'OPEN_SOURCE',
            'COMMERCIAL',
            'CUSTOMER',
            'THIRD_PARTY'
        )
    ),
    licence_name TEXT,
    licence_version TEXT,
    licensor TEXT,
    licensee TEXT,
    permitted_use TEXT,
    restrictions TEXT,
    source_url TEXT,
    document_id TEXT,
    document_version_id TEXT,
    effective_from TEXT,
    expires_at TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('DRAFT','ACTIVE','EXPIRED','REVOKED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE TABLE IF NOT EXISTS ip_contractual_assignments (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    assignor_owner_id TEXT,
    assignee_owner_id TEXT NOT NULL,
    assignment_type TEXT NOT NULL CHECK (
        assignment_type IN (
            'IP_ASSIGNMENT',
            'WORK_PRODUCT_ASSIGNMENT',
            'LICENCE',
            'CONFIDENTIALITY'
        )
    ),
    document_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('DRAFT','ACTIVE','EXPIRED','REVOKED')),
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (assignor_owner_id) REFERENCES ip_owners(id),
    FOREIGN KEY (assignee_owner_id) REFERENCES ip_owners(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE TABLE IF NOT EXISTS ip_confidentiality_records (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    party_name TEXT NOT NULL,
    confidentiality_type TEXT NOT NULL CHECK (
        confidentiality_type IN (
            'NDA',
            'CONTRACTUAL',
            'EMPLOYEE',
            'CONTRACTOR',
            'CUSTOMER'
        )
    ),
    document_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    expires_at TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('DRAFT','ACTIVE','EXPIRED','TERMINATED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (owner_id) REFERENCES ip_owners(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE TABLE IF NOT EXISTS ip_third_party_components (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    component_name TEXT NOT NULL,
    component_version TEXT,
    supplier TEXT,
    licence_id TEXT,
    source_url TEXT,
    usage_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (licence_id) REFERENCES ip_licences(id)
);

CREATE TABLE IF NOT EXISTS ip_asset_documents (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL,
    document_role TEXT NOT NULL CHECK (
        document_role IN (
            'OWNERSHIP',
            'ASSIGNMENT',
            'LICENCE',
            'NDA',
            'REGISTRATION',
            'EVIDENCE',
            'OTHER'
        )
    ),
    created_at TEXT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES ip_assets(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE INDEX IF NOT EXISTS ix_ip_assets_owner
    ON ip_assets(owner_id);

CREATE INDEX IF NOT EXISTS ix_ip_assets_type
    ON ip_assets(asset_type);

CREATE INDEX IF NOT EXISTS ix_ip_licences_asset
    ON ip_licences(asset_id);

CREATE INDEX IF NOT EXISTS ix_ip_assignments_asset
    ON ip_contractual_assignments(asset_id);

CREATE INDEX IF NOT EXISTS ix_ip_confidentiality_asset
    ON ip_confidentiality_records(asset_id);

CREATE INDEX IF NOT EXISTS ix_ip_components_asset
    ON ip_third_party_components(asset_id);
