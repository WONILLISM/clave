"""CRUD repository for overlay DB. All functions take an aiosqlite.Connection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import aiosqlite

from clave.models import (
    ArtifactListItem,
    ArtifactRow,
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


async def list_artifacts_for_session(
    conn: aiosqlite.Connection, session_id: str
) -> list[ArtifactRow]:
    cur = await conn.execute(
        """
        SELECT artifact_id, session_id, path, tool_name, message_uuid, created_at
        FROM artifacts
        WHERE session_id = ?
        ORDER BY created_at ASC, artifact_id ASC
        """,
        (session_id,),
    )
    # exists 는 API 레이어에서 계산하므로 여기선 placeholder(False).
    return [
        ArtifactRow(
            artifact_id=r["artifact_id"],
            session_id=r["session_id"],
            path=r["path"],
            tool_name=r["tool_name"],
            message_uuid=r["message_uuid"],
            created_at=r["created_at"],
            exists=False,
        )
        for r in await cur.fetchall()
    ]


async def list_all_artifacts(
    conn: aiosqlite.Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    tool_filter: str | None = None,
    path_contains: str | None = None,
) -> list[ArtifactListItem]:
    """전역 카탈로그. 세션 요약·cwd 조인하여 반환. 최신 created_at DESC."""
    clauses: list[str] = []
    params: list[Any] = []
    if tool_filter:
        clauses.append("a.tool_name = ?")
        params.append(tool_filter)
    if path_contains:
        clauses.append("a.path LIKE ?")
        params.append(f"%{path_contains}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.extend([limit, offset])
    cur = await conn.execute(
        f"""
        SELECT a.artifact_id, a.session_id, a.path, a.tool_name, a.message_uuid,
               a.created_at, s.summary AS session_summary, p.decoded_cwd AS session_decoded_cwd
        FROM artifacts a
        JOIN sessions s ON s.session_id = a.session_id
        LEFT JOIN projects p ON p.project_id = s.project_id
        {where}
        ORDER BY a.created_at DESC, a.artifact_id DESC
        LIMIT ? OFFSET ?
        """,
        params,
    )
    return [
        ArtifactListItem(
            artifact_id=r["artifact_id"],
            session_id=r["session_id"],
            path=r["path"],
            tool_name=r["tool_name"],
            message_uuid=r["message_uuid"],
            created_at=r["created_at"],
            exists=False,
            session_summary=r["session_summary"],
            session_decoded_cwd=r["session_decoded_cwd"],
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
