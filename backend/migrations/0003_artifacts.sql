-- W4-A: Artifact 스캐너 — 세션이 Write/Edit/MultiEdit로 만든 파일 카탈로그.

CREATE TABLE artifacts (
    artifact_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT    NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    path         TEXT    NOT NULL,
    tool_name    TEXT    NOT NULL,          -- 'Write' | 'Edit' | 'MultiEdit'
    message_uuid TEXT,                      -- 해당 tool_use 가 속한 message uuid (jsonl 원본)
    created_at   TEXT    NOT NULL,          -- message timestamp, fallback = indexed_at
    indexed_at   TEXT    NOT NULL
);

CREATE INDEX idx_artifacts_session ON artifacts(session_id, created_at DESC);
CREATE INDEX idx_artifacts_path    ON artifacts(path);

-- 재스캔 시 동일 (session, path, tool, message) 중복 방지.
-- message_uuid NULL 은 빈 문자열로 치환하여 UNIQUE 하게 비교.
CREATE UNIQUE INDEX idx_artifacts_dedup
    ON artifacts(session_id, path, tool_name, COALESCE(message_uuid, ''));

-- 기존 세션 재스캔 유도: signature(size) 무효화하여 다음 부트스트랩에서 artifact 백필.
-- bootstrap.scan_project() 의 skip 로직이 (size, mtime) 동일성에 의존하므로 size 만 어긋나게 하면 된다.
UPDATE sessions SET file_size = -1;

INSERT INTO schema_version VALUES (3, datetime('now'));
