-- Clave overlay DB schema v1.

CREATE TABLE schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL
);

CREATE TABLE projects (
    project_id     TEXT PRIMARY KEY,
    decoded_cwd    TEXT NOT NULL,
    cwd_exists     INTEGER NOT NULL DEFAULT 0,
    first_seen_at  TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    session_count  INTEGER NOT NULL DEFAULT 0,
    indexed_at     TEXT NOT NULL
);

CREATE TABLE sessions (
    session_id              TEXT PRIMARY KEY,
    project_id              TEXT NOT NULL REFERENCES projects(project_id),
    jsonl_path              TEXT NOT NULL,
    started_at              TEXT NOT NULL,
    last_message_at         TEXT NOT NULL,
    message_count           INTEGER NOT NULL DEFAULT 0,
    user_message_count      INTEGER NOT NULL DEFAULT 0,
    assistant_message_count INTEGER NOT NULL DEFAULT 0,
    tool_use_count          INTEGER NOT NULL DEFAULT 0,
    subagent_count          INTEGER NOT NULL DEFAULT 0,
    summary                 TEXT,
    git_branch              TEXT,
    cc_version              TEXT,
    file_size               INTEGER NOT NULL,
    file_mtime              TEXT NOT NULL,
    indexed_at              TEXT NOT NULL
);
CREATE INDEX idx_sessions_project ON sessions(project_id, last_message_at DESC);
CREATE INDEX idx_sessions_last    ON sessions(last_message_at DESC);

CREATE TABLE pins (
    session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    pinned_at  TEXT NOT NULL
);

CREATE TABLE tags (
    tag_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    color      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE session_tags (
    session_id TEXT    NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    tag_id     INTEGER NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
    tagged_at  TEXT    NOT NULL,
    PRIMARY KEY (session_id, tag_id)
);

CREATE TABLE notes (
    note_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    body       TEXT    NOT NULL,
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);
CREATE INDEX idx_notes_session ON notes(session_id, created_at DESC);

INSERT INTO schema_version VALUES (1, datetime('now'));
