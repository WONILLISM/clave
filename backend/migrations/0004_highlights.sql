-- W4-B: Highlight — 세션 메시지에서 사용자가 선택·저장한 텍스트 인용.

CREATE TABLE highlights (
    highlight_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT    NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    message_uuid  TEXT,                              -- 선택이 속한 메시지 uuid (메시지로 점프용)
    text          TEXT    NOT NULL,                  -- 선택된 원본 텍스트
    kind          TEXT    NOT NULL DEFAULT 'insight',-- 추후 'prompt'|'recipe'|'snippet' 확장 여지
    created_at    TEXT    NOT NULL
);

CREATE INDEX idx_highlights_session ON highlights(session_id, created_at DESC);
CREATE INDEX idx_highlights_kind    ON highlights(kind);

INSERT INTO schema_version VALUES (4, datetime('now'));
