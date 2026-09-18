PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO permissions(id,code,name,created_at)
VALUES
('00000000-0000-4000-8000-000000000291','documents.file.create','Create documents and files',datetime('now')),
('00000000-0000-4000-8000-000000000292','documents.file.read','Read documents and files',datetime('now')),
('00000000-0000-4000-8000-000000000293','documents.file.update','Update documents and files',datetime('now')),
('00000000-0000-4000-8000-000000000294','documents.file.delete','Delete documents and files',datetime('now')),
('00000000-0000-4000-8000-000000000295','documents.attachment.manage','Manage document attachments',datetime('now'));

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    storage_key TEXT NOT NULL,
    checksum TEXT,
    context_type TEXT,
    context_id TEXT,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','ARCHIVED','DELETED')),
    created_by_identity_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (created_by_identity_id) REFERENCES identities(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_org
ON documents(organisation_id);

CREATE INDEX IF NOT EXISTS idx_documents_context
ON documents(organisation_id,context_type,context_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_org_storage_key
ON documents(organisation_id,storage_key);

CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    storage_key TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    checksum TEXT,
    created_by_identity_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (created_by_identity_id) REFERENCES identities(id),
    UNIQUE(document_id,version_number)
);

CREATE INDEX IF NOT EXISTS idx_document_versions_document
ON document_versions(document_id,version_number);

CREATE TABLE IF NOT EXISTS document_attachments (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    context_type TEXT NOT NULL,
    context_id TEXT NOT NULL,
    attached_by_identity_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (attached_by_identity_id) REFERENCES identities(id),
    UNIQUE(organisation_id,document_id,context_type,context_id)
);

CREATE INDEX IF NOT EXISTS idx_document_attachments_context
ON document_attachments(organisation_id,context_type,context_id);

CREATE INDEX IF NOT EXISTS idx_document_attachments_document
ON document_attachments(organisation_id,document_id);
