-- FTS5 검색 지원: sessions에 file_paths 컬럼 + contentless FTS5 가상 테이블.

ALTER TABLE sessions ADD COLUMN file_paths TEXT NOT NULL DEFAULT '';

CREATE VIRTUAL TABLE sessions_fts USING fts5(
    summary,
    file_paths,
    decoded_cwd,
    content=''
);

-- 기존 데이터를 FTS 인덱스에 삽입.
INSERT INTO sessions_fts(rowid, summary, file_paths, decoded_cwd)
SELECT s.rowid, COALESCE(s.summary, ''), '', COALESCE(p.decoded_cwd, '')
FROM sessions s LEFT JOIN projects p ON p.project_id = s.project_id;

INSERT INTO schema_version VALUES (2, datetime('now'));
