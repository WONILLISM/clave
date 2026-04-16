-- W6: Knowledge Graph — 통합 노드/엣지 그래프 + 지식 링크.

CREATE TABLE knowledge_items (
    knowledge_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    body          TEXT    NOT NULL DEFAULT '',
    kind          TEXT    NOT NULL DEFAULT 'insight',
    source_type   TEXT,          -- 생성 출처 노드 타입 (예: 'session', 'highlight')
    source_id     TEXT,          -- 생성 출처 노드 id
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL
);
CREATE INDEX idx_knowledge_kind    ON knowledge_items(kind);
CREATE INDEX idx_knowledge_source  ON knowledge_items(source_type, source_id);
CREATE INDEX idx_knowledge_updated ON knowledge_items(updated_at DESC);

CREATE TABLE knowledge_links (
    link_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    from_type  TEXT NOT NULL,   -- 'knowledge' | 'session' | 'highlight' | 'note'
    from_id    TEXT NOT NULL,
    to_type    TEXT NOT NULL,
    to_id      TEXT NOT NULL,
    relation   TEXT NOT NULL DEFAULT 'related',
    created_at TEXT NOT NULL,
    UNIQUE(from_type, from_id, to_type, to_id)
);
CREATE INDEX idx_links_from ON knowledge_links(from_type, from_id);
CREATE INDEX idx_links_to   ON knowledge_links(to_type, to_id);

CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    title, body, content='', tokenize='unicode61'
);

INSERT INTO schema_version VALUES (5, datetime('now'));
