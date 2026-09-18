PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO permissions(id,code,name,created_at)
VALUES
('00000000-0000-4000-8000-000000000281','communications.channel.create','Create communication channels',datetime('now')),
('00000000-0000-4000-8000-000000000282','communications.channel.manage_members','Manage communication channel members',datetime('now')),
('00000000-0000-4000-8000-000000000283','communications.message.send','Send communication messages',datetime('now')),
('00000000-0000-4000-8000-000000000284','communications.message.react','React to communication messages',datetime('now')),
('00000000-0000-4000-8000-000000000285','communications.message.read','Read communication messages',datetime('now')),
('00000000-0000-4000-8000-000000000286','communications.presence.update','Update communication presence',datetime('now'));

CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    organisation_id TEXT NOT NULL,
    channel_type TEXT NOT NULL,
    name TEXT NOT NULL,
    direct_key TEXT,
    visibility TEXT NOT NULL CHECK (visibility IN ('PRIVATE','ORG')),
    created_by_identity_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE','ARCHIVED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (created_by_identity_id) REFERENCES identities(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_channels_org_name
ON channels(organisation_id,name)
WHERE channel_type <> 'DIRECT';

CREATE UNIQUE INDEX IF NOT EXISTS uq_channels_org_direct_key
ON channels(organisation_id,direct_key)
WHERE channel_type = 'DIRECT' AND direct_key IS NOT NULL;


CREATE TABLE IF NOT EXISTS channel_members (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','REMOVED')),
    joined_at TEXT NOT NULL,
    UNIQUE(channel_id,identity_id),
    FOREIGN KEY(channel_id) REFERENCES channels(id),
    FOREIGN KEY(identity_id) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    sender_identity_id TEXT NOT NULL,
    content TEXT NOT NULL,
    parent_message_id TEXT,
    context_type TEXT,
    context_id TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','EDITED','DELETED')),
    created_at TEXT NOT NULL,
    edited_at TEXT,
    FOREIGN KEY(channel_id) REFERENCES channels(id),
    FOREIGN KEY(sender_identity_id) REFERENCES identities(id),
    FOREIGN KEY(parent_message_id) REFERENCES messages(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_channel_created
ON messages(channel_id,created_at);

CREATE TABLE IF NOT EXISTS message_reactions (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    reaction TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(message_id,identity_id,reaction),
    FOREIGN KEY(message_id) REFERENCES messages(id),
    FOREIGN KEY(identity_id) REFERENCES identities(id)
);

CREATE TABLE IF NOT EXISTS message_read_states (
    channel_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    last_read_message_id TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(channel_id,identity_id),
    FOREIGN KEY(channel_id) REFERENCES channels(id),
    FOREIGN KEY(identity_id) REFERENCES identities(id),
    FOREIGN KEY(last_read_message_id) REFERENCES messages(id)
);

CREATE TABLE IF NOT EXISTS presence_states (
    organisation_id TEXT NOT NULL,
    identity_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ONLINE','AWAY','OFFLINE')),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (organisation_id, identity_id),
    FOREIGN KEY(organisation_id) REFERENCES organisations(id),
    FOREIGN KEY(identity_id) REFERENCES identities(id)
);
