PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS identities (
    id TEXT PRIMARY KEY,
    identity_type TEXT NOT NULL CHECK (identity_type IN ('HUMAN','SERVICE','INTEGRATION')),
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','DISABLED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','DISABLED')),
    platform_level TEXT NOT NULL DEFAULT 'COMPANY_USER' CHECK (platform_level IN ('SYSTEM_ADMIN','COMPANY_ADMIN','COMPANY_USER')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (identity_id) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS organisations (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','CLOSED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS organisation_memberships (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL,
    organisation_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','REMOVED')),
    created_at TEXT NOT NULL,
    UNIQUE(identity_id, organisation_id),
    FOREIGN KEY (identity_id) REFERENCES identities(id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    scope TEXT NOT NULL CHECK (scope IN ('SYSTEM','ORGANISATION')),
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','DISABLED')),
    created_at TEXT NOT NULL,
    UNIQUE(organisation_id, code),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_assignments (
    id TEXT PRIMARY KEY,
    membership_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(membership_id, role_id),
    FOREIGN KEY (membership_id) REFERENCES organisation_memberships(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id TEXT NOT NULL,
    permission_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    identity_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','REVOKED','EXPIRED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (identity_id) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('REGISTERED','ENABLED','DISABLED','RETIRED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS module_entitlements (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','SUSPENDED','REVOKED')),
    created_at TEXT NOT NULL,
    UNIQUE(organisation_id, module_id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    organisation_id TEXT,
    identity_id TEXT,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    request_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (identity_id) REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_membership_identity ON organisation_memberships(identity_id);
CREATE INDEX IF NOT EXISTS idx_membership_org ON organisation_memberships(organisation_id);
CREATE INDEX IF NOT EXISTS idx_role_assignment_membership ON role_assignments(membership_id);
CREATE INDEX IF NOT EXISTS idx_session_identity ON sessions(identity_id);
CREATE INDEX IF NOT EXISTS idx_audit_org_created ON audit_events(organisation_id, created_at);
