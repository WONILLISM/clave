"""CRUD repository for overlay DB. All functions take an aiosqlite.Connection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import aiosqlite

from clave.models import (
    ArtifactPathItem,
    ArtifactSessionRef,
    HighlightRow,
    KnowledgeLinkRow,
    KnowledgeRow,
    NoteRow,
    ProjectListItem,
    ProjectRow,
    SearchResponse,
    SessionListItem,
    SessionRow,
    TagListItem,
    TagRow,
)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


# ---------- Projects ----------


async def upsert_project(conn: aiosqlite.Connection, row: ProjectRow) -> None:
    await conn.execute(
        """
        INSERT INTO projects (project_id, decoded_cwd, cwd_exists, first_seen_at,
                              last_active_at, session_count, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            decoded_cwd    = excluded.decoded_cwd,
            cwd_exists     = excluded.cwd_exists,
            first_seen_at  = MIN(projects.first_seen_at, excluded.first_seen_at),
            last_active_at = MAX(projects.last_active_at, excluded.last_active_at),
            session_count  = excluded.session_count,
            indexed_at     = excluded.indexed_at
        """,
        (
            row.project_id,
            row.decoded_cwd,
            int(row.cwd_exists),
            row.first_seen_at,
            row.last_active_at,
            row.session_count,
            row.indexed_at,
        ),
    )


async def list_projects(conn: aiosqlite.Connection) -> list[ProjectListItem]:
    cur = await conn.execute(
        "SELECT project_id, decoded_cwd, cwd_exists, session_count, last_active_at "
        "FROM projects ORDER BY last_active_at DESC"
    )
    rows = await cur.fetchall()
    return [
        ProjectListItem(
            project_id=r["project_id"],
            decoded_cwd=r["decoded_cwd"],
            cwd_exists=bool(r["cwd_exists"]),
            session_count=r["session_count"],
            last_active_at=r["last_active_at"],
        )
        for r in rows
    ]


# ---------- Sessions ----------


async def upsert_session(
    conn: aiosqlite.Connection, row: SessionRow, decoded_cwd: str = ""
) -> None:
    # Capture old FTS values BEFORE upsert (for contentless FTS5 delete).
    cur = await conn.execute(
        """
        SELECT s.rowid, COALESCE(s.summary, ''), COALESCE(s.file_paths, ''),
               COALESCE(pr.decoded_cwd, '')
        FROM sessions s
        JOIN projects pr ON pr.project_id = s.project_id
        WHERE s.session_id = ?
        """,
        (row.session_id,),
    )
    old_fts = await cur.fetchone()

    await conn.execute(
        """
        INSERT INTO sessions (
            session_id, project_id, jsonl_path, started_at, last_message_at,
            message_count, user_message_count, assistant_message_count,
            tool_use_count, subagent_count, summary, git_branch, cc_version,
            file_paths, file_size, file_mtime, indexed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            jsonl_path              = excluded.jsonl_path,
            started_at              = excluded.started_at,
            last_message_at         = excluded.last_message_at,
            message_count           = excluded.message_count,
            user_message_count      = excluded.user_message_count,
            assistant_message_count = excluded.assistant_message_count,
            tool_use_count          = excluded.tool_use_count,
            subagent_count          = excluded.subagent_count,
            summary                 = excluded.summary,
            git_branch              = excluded.git_branch,
            cc_version              = excluded.cc_version,
            file_paths              = excluded.file_paths,
            file_size               = excluded.file_size,
            file_mtime              = excluded.file_mtime,
            indexed_at              = excluded.indexed_at
        """,
        (
            row.session_id,
            row.project_id,
            row.jsonl_path,
            row.started_at,
            row.last_message_at,
            row.message_count,
            row.user_message_count,
            row.assistant_message_count,
            row.tool_use_count,
            row.subagent_count,
            row.summary,
            row.git_branch,
            row.cc_version,
            row.file_paths,
            row.file_size,
            row.file_mtime,
            row.indexed_at,
        ),
    )
    # Sync FTS5 contentless index.
    cur = await conn.execute("SELECT rowid FROM sessions WHERE session_id = ?", (row.session_id,))
    rowid_row = await cur.fetchone()
    if rowid_row:
        rowid = rowid_row[0]
        if old_fts:
            # Delete old entry (contentless FTS5 requires original values).
            await conn.execute(
                "INSERT INTO sessions_fts(sessions_fts, rowid, summary, file_paths, decoded_cwd) "
                "VALUES('delete', ?, ?, ?, ?)",
                (old_fts[0], old_fts[1], old_fts[2], old_fts[3]),
            )
        await conn.execute(
            "INSERT INTO sessions_fts(rowid, summary, file_paths, decoded_cwd) VALUES (?, ?, ?, ?)",
            (rowid, row.summary or "", row.file_paths, decoded_cwd),
        )


async def get_session_signature(
    conn: aiosqlite.Connection, session_id: str
) -> tuple[int, str] | None:
    """Return (file_size, file_mtime) for incremental-skip key, or None if absent."""
    cur = await conn.execute(
        "SELECT file_size, file_mtime FROM sessions WHERE session_id = ?", (session_id,)
    )
    row = await cur.fetchone()
    if row is None:
        return None
    return (int(row["file_size"]), str(row["file_mtime"]))


async def get_session(conn: aiosqlite.Connection, session_id: str) -> SessionRow | None:
    cur = await conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    r = await cur.fetchone()
    if r is None:
        return None
    return SessionRow(**dict(r))


async def count_sessions(conn: aiosqlite.Connection) -> int:
    cur = await conn.execute("SELECT COUNT(*) FROM sessions")
    row = await cur.fetchone()
    return int(row[0])


async def list_sessions(
    conn: aiosqlite.Connection,
    *,
    project_id: str | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
    pinned: bool | None = None,
    tag: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> tuple[list[SessionListItem], str | None]:
    """Cursor-paginated list ordered by last_message_at DESC.

    Cursor format: "<last_message_at>|<session_id>" (opaque to caller).
    """
    where: list[str] = []
    params: list[Any] = []

    if project_id:
        where.append("s.project_id = ?")
        params.append(project_id)
    if from_ts:
        where.append("s.last_message_at >= ?")
        params.append(from_ts)
    if to_ts:
        where.append("s.last_message_at <= ?")
        params.append(to_ts)
    if pinned is True:
        where.append("p.session_id IS NOT NULL")
    elif pinned is False:
        where.append("p.session_id IS NULL")
    if tag:
        where.append(
            "EXISTS (SELECT 1 FROM session_tags st JOIN tags t ON t.tag_id = st.tag_id "
            "WHERE st.session_id = s.session_id AND t.name = ?)"
        )
        params.append(tag)
    if cursor:
        try:
            cur_ts, cur_sid = cursor.split("|", 1)
        except ValueError as e:
            raise ValueError(f"invalid cursor: {cursor!r}") from e
        where.append("(s.last_message_at, s.session_id) < (?, ?)")
        params.extend([cur_ts, cur_sid])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT s.*, pr.decoded_cwd,
               (p.session_id IS NOT NULL) AS is_pinned
        FROM sessions s
        JOIN projects pr ON pr.project_id = s.project_id
        LEFT JOIN pins p ON p.session_id = s.session_id
        {where_sql}
        ORDER BY s.last_message_at DESC, s.session_id DESC
        LIMIT ?
    """
    params.append(limit + 1)
    cur = await conn.execute(sql, params)
    rows = await cur.fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]

    # Fetch tag lists for the page (one query, then group in Python).
    sids = [r["session_id"] for r in rows]
    tags_map: dict[str, list[str]] = {sid: [] for sid in sids}
    if sids:
        placeholders = ",".join("?" * len(sids))
        cur = await conn.execute(
            f"""
            SELECT st.session_id, t.name
            FROM session_tags st JOIN tags t ON t.tag_id = st.tag_id
            WHERE st.session_id IN ({placeholders})
            ORDER BY t.name
            """,
            sids,
        )
        for tr in await cur.fetchall():
            tags_map[tr["session_id"]].append(tr["name"])

    items = [
        SessionListItem(
            session_id=r["session_id"],
            project_id=r["project_id"],
            decoded_cwd=r["decoded_cwd"],
            started_at=r["started_at"],
            last_message_at=r["last_message_at"],
            message_count=r["message_count"],
            user_message_count=r["user_message_count"],
            assistant_message_count=r["assistant_message_count"],
            tool_use_count=r["tool_use_count"],
            subagent_count=r["subagent_count"],
            summary=r["summary"],
            git_branch=r["git_branch"],
            cc_version=r["cc_version"],
            pinned=bool(r["is_pinned"]),
            tags=tags_map.get(r["session_id"], []),
        )
        for r in rows
    ]
    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.last_message_at}|{last.session_id}"
    return items, next_cursor


async def get_session_list_item(
    conn: aiosqlite.Connection, session_id: str
) -> SessionListItem | None:
    """Same shape as list_sessions items, for a single id."""
    cur = await conn.execute(
        """
        SELECT s.*, pr.decoded_cwd, (p.session_id IS NOT NULL) AS is_pinned
        FROM sessions s
        JOIN projects pr ON pr.project_id = s.project_id
        LEFT JOIN pins p ON p.session_id = s.session_id
        WHERE s.session_id = ?
        """,
        (session_id,),
    )
    r = await cur.fetchone()
    if r is None:
        return None
    cur = await conn.execute(
        """
        SELECT t.name FROM session_tags st JOIN tags t ON t.tag_id = st.tag_id
        WHERE st.session_id = ? ORDER BY t.name
        """,
        (session_id,),
    )
    tags = [tr["name"] for tr in await cur.fetchall()]
    return SessionListItem(
        session_id=r["session_id"],
        project_id=r["project_id"],
        decoded_cwd=r["decoded_cwd"],
        started_at=r["started_at"],
        last_message_at=r["last_message_at"],
        message_count=r["message_count"],
        user_message_count=r["user_message_count"],
        assistant_message_count=r["assistant_message_count"],
        tool_use_count=r["tool_use_count"],
        subagent_count=r["subagent_count"],
        summary=r["summary"],
        git_branch=r["git_branch"],
        cc_version=r["cc_version"],
        pinned=bool(r["is_pinned"]),
        tags=tags,
    )


# ---------- Pins ----------


async def add_pin(conn: aiosqlite.Connection, session_id: str) -> None:
    await conn.execute(
        "INSERT OR IGNORE INTO pins (session_id, pinned_at) VALUES (?, ?)",
        (session_id, _now()),
    )


async def remove_pin(conn: aiosqlite.Connection, session_id: str) -> None:
    await conn.execute("DELETE FROM pins WHERE session_id = ?", (session_id,))


# ---------- Tags ----------


async def list_tags(conn: aiosqlite.Connection) -> list[TagListItem]:
    cur = await conn.execute(
        """
        SELECT t.tag_id, t.name, t.color,
               (SELECT COUNT(*) FROM session_tags st WHERE st.tag_id = t.tag_id) AS session_count
        FROM tags t ORDER BY t.name
        """
    )
    rows = await cur.fetchall()
    return [
        TagListItem(
            tag_id=r["tag_id"],
            name=r["name"],
            color=r["color"],
            session_count=r["session_count"],
        )
        for r in rows
    ]


async def create_tag(conn: aiosqlite.Connection, name: str, color: str | None) -> TagRow:
    await conn.execute(
        "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?) ON CONFLICT(name) DO NOTHING",
        (name, color, _now()),
    )
    cur = await conn.execute("SELECT * FROM tags WHERE name = ?", (name,))
    r = await cur.fetchone()
    assert r is not None
    return TagRow(**dict(r))


async def attach_tag(conn: aiosqlite.Connection, session_id: str, tag_id: int) -> None:
    await conn.execute(
        "INSERT OR IGNORE INTO session_tags (session_id, tag_id, tagged_at) VALUES (?, ?, ?)",
        (session_id, tag_id, _now()),
    )


async def detach_tag(conn: aiosqlite.Connection, session_id: str, tag_id: int) -> None:
    await conn.execute(
        "DELETE FROM session_tags WHERE session_id = ? AND tag_id = ?",
        (session_id, tag_id),
    )


async def get_tag_by_name(conn: aiosqlite.Connection, name: str) -> TagRow | None:
    cur = await conn.execute("SELECT * FROM tags WHERE name = ?", (name,))
    r = await cur.fetchone()
    return TagRow(**dict(r)) if r else None


# ---------- Notes ----------


async def list_notes(conn: aiosqlite.Connection, session_id: str) -> list[NoteRow]:
    cur = await conn.execute(
        "SELECT * FROM notes WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,),
    )
    return [NoteRow(**dict(r)) for r in await cur.fetchall()]


async def create_note(conn: aiosqlite.Connection, session_id: str, body: str) -> NoteRow:
    now = _now()
    cur = await conn.execute(
        "INSERT INTO notes (session_id, body, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, body, now, now),
    )
    note_id = cur.lastrowid
    return NoteRow(
        note_id=note_id,
        session_id=session_id,
        body=body,
        created_at=now,
        updated_at=now,
    )


async def update_note(conn: aiosqlite.Connection, note_id: int, body: str) -> NoteRow | None:
    now = _now()
    cur = await conn.execute(
        "UPDATE notes SET body = ?, updated_at = ? WHERE note_id = ?",
        (body, now, note_id),
    )
    if cur.rowcount == 0:
        return None
    cur = await conn.execute("SELECT * FROM notes WHERE note_id = ?", (note_id,))
    r = await cur.fetchone()
    return NoteRow(**dict(r)) if r else None


async def delete_note(conn: aiosqlite.Connection, note_id: int) -> bool:
    cur = await conn.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
    return cur.rowcount > 0


# ---------- Highlights ----------


async def list_highlights(conn: aiosqlite.Connection, session_id: str) -> list[HighlightRow]:
    cur = await conn.execute(
        "SELECT * FROM highlights WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,),
    )
    return [HighlightRow(**dict(r)) for r in await cur.fetchall()]


async def create_highlight(
    conn: aiosqlite.Connection,
    session_id: str,
    message_uuid: str | None,
    text: str,
    kind: str,
) -> HighlightRow:
    now = _now()
    cur = await conn.execute(
        "INSERT INTO highlights (session_id, message_uuid, text, kind, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, message_uuid, text, kind, now),
    )
    highlight_id = cur.lastrowid
    assert highlight_id is not None
    return HighlightRow(
        highlight_id=highlight_id,
        session_id=session_id,
        message_uuid=message_uuid,
        text=text,
        kind=kind,
        created_at=now,
    )


async def delete_highlight(conn: aiosqlite.Connection, highlight_id: int) -> bool:
    cur = await conn.execute("DELETE FROM highlights WHERE highlight_id = ?", (highlight_id,))
    return cur.rowcount > 0


# ---------- Artifacts ----------


async def delete_artifacts_for_session(conn: aiosqlite.Connection, session_id: str) -> None:
    """재스캔 직전, 해당 세션의 artifact 행을 전부 비움 (delete-then-insert 패턴)."""
    await conn.execute("DELETE FROM artifacts WHERE session_id = ?", (session_id,))


async def bulk_insert_artifacts(
    conn: aiosqlite.Connection,
    session_id: str,
    artifacts: list[tuple[str, str, str | None, str | None]],
    indexed_at: str,
) -> int:
    """artifacts 튜플 (path, tool_name, message_uuid, created_at) 목록을 executemany 로 삽입.

    created_at 이 None 이면 indexed_at 로 폴백.
    반환: 삽입된 행 수.
    """
    if not artifacts:
        return 0
    rows = [
        (session_id, path, tool_name, message_uuid, created_at or indexed_at, indexed_at)
        for (path, tool_name, message_uuid, created_at) in artifacts
    ]
    await conn.executemany(
        """
        INSERT OR IGNORE INTO artifacts
            (session_id, path, tool_name, message_uuid, created_at, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


async def list_artifact_paths(
    conn: aiosqlite.Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    path_contains: str | None = None,
) -> list[ArtifactPathItem]:
    """Path 중심 카탈로그. GROUP BY path — 1 path = 1 항목.

    각 항목은 편집 횟수, 고유 세션 수, tool 분포, 마지막 수정 시각/세션 요약을 포함한다.
    exists 는 placeholder(False) 로 채우고 API 레이어에서 os.path.exists 로 채운다.
    """
    clauses: list[str] = []
    params: list[Any] = []
    if path_contains:
        clauses.append("a.path LIKE ?")
        params.append(f"%{path_contains}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.extend([limit, offset])
    # last_session_id 는 상관 서브쿼리로 — path 당 created_at DESC 의 첫 session_id.
    # last_session_summary 는 바깥 LEFT JOIN 으로 받음.
    cur = await conn.execute(
        f"""
        SELECT
            a.path                                        AS path,
            MAX(a.created_at)                             AS last_modified,
            COUNT(*)                                      AS edit_count,
            COUNT(DISTINCT a.session_id)                  AS session_count,
            GROUP_CONCAT(DISTINCT a.tool_name)            AS tools_csv,
            (
                SELECT a2.session_id FROM artifacts a2
                WHERE a2.path = a.path
                ORDER BY a2.created_at DESC, a2.artifact_id DESC
                LIMIT 1
            )                                             AS last_session_id
        FROM artifacts a
        {where}
        GROUP BY a.path
        ORDER BY last_modified DESC
        LIMIT ? OFFSET ?
        """,
        params,
    )
    rows = await cur.fetchall()
    if not rows:
        return []
    # summary 를 한 번에 가져오기 위한 IN 쿼리.
    session_ids = list({r["last_session_id"] for r in rows if r["last_session_id"]})
    summary_by_id: dict[str, str | None] = {}
    if session_ids:
        placeholders = ",".join(["?"] * len(session_ids))
        cur2 = await conn.execute(
            f"SELECT session_id, summary FROM sessions WHERE session_id IN ({placeholders})",
            session_ids,
        )
        for r in await cur2.fetchall():
            summary_by_id[r["session_id"]] = r["summary"]

    return [
        ArtifactPathItem(
            path=r["path"],
            last_modified=r["last_modified"],
            edit_count=r["edit_count"],
            session_count=r["session_count"],
            tools=sorted((r["tools_csv"] or "").split(",")) if r["tools_csv"] else [],
            last_session_id=r["last_session_id"],
            last_session_summary=summary_by_id.get(r["last_session_id"]),
            exists=False,
        )
        for r in rows
    ]


async def list_sessions_for_artifact_path(
    conn: aiosqlite.Connection,
    path: str,
    *,
    limit: int = 30,
    offset: int = 0,
) -> list[ArtifactSessionRef]:
    """특정 path 를 건드린 세션들. MAX(created_at) DESC 로 정렬."""
    cur = await conn.execute(
        """
        SELECT
            a.session_id                         AS session_id,
            s.summary                            AS session_summary,
            p.decoded_cwd                        AS decoded_cwd,
            MAX(a.created_at)                    AS created_at,
            COUNT(*)                             AS edit_count,
            (
                SELECT a2.tool_name FROM artifacts a2
                WHERE a2.session_id = a.session_id AND a2.path = ?
                ORDER BY a2.created_at DESC, a2.artifact_id DESC
                LIMIT 1
            )                                    AS tool_name,
            (
                SELECT a2.message_uuid FROM artifacts a2
                WHERE a2.session_id = a.session_id AND a2.path = ?
                ORDER BY a2.created_at DESC, a2.artifact_id DESC
                LIMIT 1
            )                                    AS message_uuid
        FROM artifacts a
        LEFT JOIN sessions s ON s.session_id = a.session_id
        LEFT JOIN projects p ON p.project_id = s.project_id
        WHERE a.path = ?
        GROUP BY a.session_id
        ORDER BY MAX(a.created_at) DESC
        LIMIT ? OFFSET ?
        """,
        (path, path, path, limit, offset),
    )
    return [
        ArtifactSessionRef(
            session_id=r["session_id"],
            session_summary=r["session_summary"],
            decoded_cwd=r["decoded_cwd"],
            tool_name=r["tool_name"],
            message_uuid=r["message_uuid"],
            created_at=r["created_at"],
            edit_count=r["edit_count"],
        )
        for r in await cur.fetchall()
    ]


# ---------- Search (FTS5) ----------


async def search_sessions(
    conn: aiosqlite.Connection,
    query: str,
    *,
    limit: int = 20,
) -> SearchResponse:
    """FTS5 MATCH on sessions_fts, returns matching sessions."""
    # FTS5 expects double-quotes around terms with special chars; wrap each token.
    tokens = query.strip().split()
    if not tokens:
        return SearchResponse(items=[], query=query)
    fts_query = " OR ".join(f'"{t}"' for t in tokens)

    cur = await conn.execute(
        """
        SELECT s.*, pr.decoded_cwd, (p.session_id IS NOT NULL) AS is_pinned
        FROM sessions_fts fts
        JOIN sessions s ON s.rowid = fts.rowid
        JOIN projects pr ON pr.project_id = s.project_id
        LEFT JOIN pins p ON p.session_id = s.session_id
        WHERE sessions_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, limit),
    )
    rows = await cur.fetchall()

    sids = [r["session_id"] for r in rows]
    tags_map: dict[str, list[str]] = {sid: [] for sid in sids}
    if sids:
        placeholders = ",".join("?" * len(sids))
        cur = await conn.execute(
            f"""
            SELECT st.session_id, t.name
            FROM session_tags st JOIN tags t ON t.tag_id = st.tag_id
            WHERE st.session_id IN ({placeholders})
            ORDER BY t.name
            """,
            sids,
        )
        for tr in await cur.fetchall():
            tags_map[tr["session_id"]].append(tr["name"])

    items = [
        SessionListItem(
            session_id=r["session_id"],
            project_id=r["project_id"],
            decoded_cwd=r["decoded_cwd"],
            started_at=r["started_at"],
            last_message_at=r["last_message_at"],
            message_count=r["message_count"],
            user_message_count=r["user_message_count"],
            assistant_message_count=r["assistant_message_count"],
            tool_use_count=r["tool_use_count"],
            subagent_count=r["subagent_count"],
            summary=r["summary"],
            git_branch=r["git_branch"],
            cc_version=r["cc_version"],
            pinned=bool(r["is_pinned"]),
            tags=tags_map.get(r["session_id"], []),
        )
        for r in rows
    ]
    return SearchResponse(items=items, query=query)


# ---------- Knowledge Items ----------


async def create_knowledge(
    conn: aiosqlite.Connection,
    title: str,
    body: str = "",
    kind: str = "insight",
    source_type: str | None = None,
    source_id: str | None = None,
) -> KnowledgeRow:
    now = _now()
    cur = await conn.execute(
        """
        INSERT INTO knowledge_items (title, body, kind, source_type, source_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (title, body, kind, source_type, source_id, now, now),
    )
    kid = cur.lastrowid
    assert kid is not None
    # FTS insert.
    await conn.execute(
        "INSERT INTO knowledge_fts(rowid, title, body) VALUES (?, ?, ?)",
        (kid, title, body),
    )
    return KnowledgeRow(
        knowledge_id=kid,
        title=title,
        body=body,
        kind=kind,
        source_type=source_type,
        source_id=source_id,
        created_at=now,
        updated_at=now,
    )


async def get_knowledge(conn: aiosqlite.Connection, knowledge_id: int) -> KnowledgeRow | None:
    cur = await conn.execute(
        "SELECT * FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,)
    )
    r = await cur.fetchone()
    if r is None:
        return None
    return KnowledgeRow(**dict(r))


async def update_knowledge(
    conn: aiosqlite.Connection,
    knowledge_id: int,
    *,
    title: str | None = None,
    body: str | None = None,
    kind: str | None = None,
) -> KnowledgeRow | None:
    # Fetch old row for FTS contentless delete.
    cur = await conn.execute(
        "SELECT * FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,)
    )
    old = await cur.fetchone()
    if old is None:
        return None

    sets: list[str] = []
    params: list[Any] = []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if body is not None:
        sets.append("body = ?")
        params.append(body)
    if kind is not None:
        sets.append("kind = ?")
        params.append(kind)
    if not sets:
        return KnowledgeRow(**dict(old))

    now = _now()
    sets.append("updated_at = ?")
    params.append(now)
    params.append(knowledge_id)
    await conn.execute(
        f"UPDATE knowledge_items SET {', '.join(sets)} WHERE knowledge_id = ?",
        params,
    )

    # FTS contentless: delete old → insert new.
    await conn.execute(
        "INSERT INTO knowledge_fts(knowledge_fts, rowid, title, body) VALUES('delete', ?, ?, ?)",
        (knowledge_id, old["title"], old["body"]),
    )
    new_title = title if title is not None else old["title"]
    new_body = body if body is not None else old["body"]
    await conn.execute(
        "INSERT INTO knowledge_fts(rowid, title, body) VALUES (?, ?, ?)",
        (knowledge_id, new_title, new_body),
    )

    cur = await conn.execute(
        "SELECT * FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,)
    )
    r = await cur.fetchone()
    return KnowledgeRow(**dict(r)) if r else None


async def delete_knowledge(conn: aiosqlite.Connection, knowledge_id: int) -> bool:
    cur = await conn.execute(
        "SELECT * FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,)
    )
    old = await cur.fetchone()
    if old is None:
        return False

    # FTS contentless delete.
    await conn.execute(
        "INSERT INTO knowledge_fts(knowledge_fts, rowid, title, body) VALUES('delete', ?, ?, ?)",
        (knowledge_id, old["title"], old["body"]),
    )
    # Clean up links (both directions).
    await conn.execute(
        "DELETE FROM knowledge_links WHERE (from_type = 'knowledge' AND from_id = ?) "
        "OR (to_type = 'knowledge' AND to_id = ?)",
        (str(knowledge_id), str(knowledge_id)),
    )
    await conn.execute("DELETE FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,))
    return True


async def list_knowledge(
    conn: aiosqlite.Connection,
    *,
    kind: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[KnowledgeRow], int]:
    where: list[str] = []
    params: list[Any] = []
    if kind:
        where.append("kind = ?")
        params.append(kind)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    cur = await conn.execute(f"SELECT COUNT(*) FROM knowledge_items {where_sql}", params)
    total = int((await cur.fetchone())[0])

    cur = await conn.execute(
        f"SELECT * FROM knowledge_items {where_sql} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    items = [KnowledgeRow(**dict(r)) for r in await cur.fetchall()]
    return items, total


async def search_knowledge(
    conn: aiosqlite.Connection,
    query: str,
    *,
    limit: int = 20,
) -> list[KnowledgeRow]:
    tokens = query.strip().split()
    if not tokens:
        return []
    fts_query = " OR ".join(f'"{t}"' for t in tokens)
    cur = await conn.execute(
        """
        SELECT ki.*
        FROM knowledge_fts fts
        JOIN knowledge_items ki ON ki.knowledge_id = fts.rowid
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, limit),
    )
    return [KnowledgeRow(**dict(r)) for r in await cur.fetchall()]


# ---------- Knowledge Links ----------


async def create_link(
    conn: aiosqlite.Connection,
    from_type: str,
    from_id: str,
    to_type: str,
    to_id: str,
    relation: str = "related",
) -> KnowledgeLinkRow | None:
    """Create a link. Returns None if duplicate (UNIQUE constraint)."""
    now = _now()
    await conn.execute(
        """
        INSERT OR IGNORE INTO knowledge_links (from_type, from_id, to_type, to_id, relation, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (from_type, from_id, to_type, to_id, relation, now),
    )
    cur = await conn.execute(
        """
        SELECT * FROM knowledge_links
        WHERE from_type = ? AND from_id = ? AND to_type = ? AND to_id = ?
        """,
        (from_type, from_id, to_type, to_id),
    )
    r = await cur.fetchone()
    return KnowledgeLinkRow(**dict(r)) if r else None


async def delete_link(conn: aiosqlite.Connection, link_id: int) -> bool:
    cur = await conn.execute("DELETE FROM knowledge_links WHERE link_id = ?", (link_id,))
    return cur.rowcount > 0


async def list_links(
    conn: aiosqlite.Connection, node_type: str, node_id: str
) -> list[KnowledgeLinkRow]:
    """Outgoing links from a node."""
    cur = await conn.execute(
        "SELECT * FROM knowledge_links WHERE from_type = ? AND from_id = ? ORDER BY created_at DESC",
        (node_type, node_id),
    )
    return [KnowledgeLinkRow(**dict(r)) for r in await cur.fetchall()]


async def list_backlinks(
    conn: aiosqlite.Connection, node_type: str, node_id: str
) -> list[KnowledgeLinkRow]:
    """Incoming links to a node."""
    cur = await conn.execute(
        "SELECT * FROM knowledge_links WHERE to_type = ? AND to_id = ? ORDER BY created_at DESC",
        (node_type, node_id),
    )
    return [KnowledgeLinkRow(**dict(r)) for r in await cur.fetchall()]


# ---------- Promote highlight → knowledge ----------


async def get_highlight(conn: aiosqlite.Connection, highlight_id: int) -> HighlightRow | None:
    cur = await conn.execute("SELECT * FROM highlights WHERE highlight_id = ?", (highlight_id,))
    r = await cur.fetchone()
    return HighlightRow(**dict(r)) if r else None


async def promote_highlight_to_knowledge(
    conn: aiosqlite.Connection,
    highlight_id: int,
    title: str | None = None,
    kind: str = "insight",
) -> KnowledgeRow | None:
    """Highlight → Knowledge 승격. 자동으로 derives_from 링크(session) 생성."""
    hl = await get_highlight(conn, highlight_id)
    if hl is None:
        return None

    effective_title = title or hl.text[:80]
    ki = await create_knowledge(
        conn,
        title=effective_title,
        body=hl.text,
        kind=kind,
        source_type="highlight",
        source_id=str(hl.highlight_id),
    )
    # Link: knowledge → session (derives_from).
    await create_link(
        conn,
        from_type="knowledge",
        from_id=str(ki.knowledge_id),
        to_type="session",
        to_id=hl.session_id,
        relation="derives_from",
    )
    return ki


# ---------- Session deletion ----------


async def delete_session(conn: aiosqlite.Connection, session_id: str) -> bool:
    """overlay DB 에서 sessions 행 삭제. CASCADE 로 자식 테이블 자동 정리.

    ~/.claude/ 는 절대 건드리지 않는다 — overlay only, ~/.claude/ untouched.

    Returns:
        True  — 행이 존재하여 삭제됨.
        False — 해당 session_id 없음 (호출자가 404 반환 가능).
    """
    # FTS5 contentless index 도 함께 정리해야 한다.
    cur = await conn.execute(
        """
        SELECT s.rowid, COALESCE(s.summary, ''), COALESCE(s.file_paths, ''),
               COALESCE(pr.decoded_cwd, '')
        FROM sessions s
        JOIN projects pr ON pr.project_id = s.project_id
        WHERE s.session_id = ?
        """,
        (session_id,),
    )
    fts_row = await cur.fetchone()
    if fts_row is None:
        return False

    # FTS5 contentless delete — 원본 값 정확히 전달 필요.
    await conn.execute(
        "INSERT INTO sessions_fts(sessions_fts, rowid, summary, file_paths, decoded_cwd) "
        "VALUES('delete', ?, ?, ?, ?)",
        (fts_row[0], fts_row[1], fts_row[2], fts_row[3]),
    )
    await conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    return True
