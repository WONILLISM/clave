"""DELETE /api/sessions/{session_id} + overlay repo.delete_session() 통합 테스트.

overlay DB 행만 삭제, ~/.claude/ 는 절대 건드리지 않음(CLAUDE.md 제약 #1).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio
from httpx import AsyncClient

from clave.app import create_app
from clave.config import PathsConfig, ScannerConfig, ServerConfig, Settings
from clave.overlay import repo
from clave.overlay.db import open_db
from clave.overlay.migrate import migrate
from clave.scanner.bootstrap import run_full_scan

# ---------- 헬퍼 ----------


def _ts(days_ago: int = 0) -> str:
    dt = datetime.now(UTC) - timedelta(days=days_ago)
    return dt.isoformat(timespec="seconds")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------- Fixtures ----------


@pytest.fixture
def del_claude_home(tmp_path: Path) -> Path:
    """세션 1개 (session-del)를 가진 fake claude_home."""
    claude_home = tmp_path / "claude"
    _write_jsonl(
        claude_home / "projects" / "-tmp-del-proj" / "session-del.jsonl",
        [
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-04-15T10:00:00.000Z",
                "sessionId": "session-del",
                "cwd": "/tmp/del-proj",
                "message": {"role": "user", "content": "delete me"},
            }
        ],
    )
    return claude_home


@pytest.fixture
def del_settings(tmp_path: Path, del_claude_home: Path) -> Settings:
    return Settings(
        paths=PathsConfig(
            claude_home=del_claude_home,
            overlay_db=tmp_path / "del-overlay.sqlite",
            trash_dir=tmp_path / "trash",
        ),
        server=ServerConfig(),
        scanner=ScannerConfig(),
    )


@pytest_asyncio.fixture
async def del_db(del_settings: Settings) -> aiosqlite.Connection:
    conn = await open_db(del_settings.paths.overlay_db)
    await migrate(conn)
    await run_full_scan(conn, del_settings.paths.claude_home)
    try:
        yield conn
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def del_client(del_settings: Settings) -> AsyncClient:
    app = create_app(del_settings)
    async with app.router.lifespan_context(app):
        from httpx import ASGITransport

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ---------- 1. 204 반환 ----------


async def test_delete_session_returns_204(del_client: AsyncClient) -> None:
    """존재하는 세션 DELETE → 204 No Content."""
    r = await del_client.delete("/api/sessions/session-del")
    assert r.status_code == 204


# ---------- 2. 없는 세션 404 ----------


async def test_delete_session_404_when_missing(del_client: AsyncClient) -> None:
    """존재하지 않는 session_id DELETE → 404."""
    r = await del_client.delete("/api/sessions/no-such-session")
    assert r.status_code == 404


# ---------- 3. sessions 행 제거 ----------


async def test_delete_removes_session_row(del_db: aiosqlite.Connection) -> None:
    """DELETE 후 sessions 테이블에 행이 없어야 함."""
    deleted = await repo.delete_session(del_db, "session-del")
    await del_db.commit()
    assert deleted is True

    cur = await del_db.execute(
        "SELECT COUNT(*) AS c FROM sessions WHERE session_id = 'session-del'"
    )
    assert (await cur.fetchone())["c"] == 0


# ---------- 4. CASCADE pins ----------


async def test_cascade_pins(del_db: aiosqlite.Connection) -> None:
    """pin 달린 세션 DELETE → pins 테이블에서도 사라짐."""
    await del_db.execute(
        "INSERT INTO pins(session_id, pinned_at) VALUES (?, ?)",
        ("session-del", _ts()),
    )
    await del_db.commit()

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    cur = await del_db.execute("SELECT COUNT(*) AS c FROM pins WHERE session_id = 'session-del'")
    assert (await cur.fetchone())["c"] == 0


# ---------- 5. CASCADE session_tags (tags 테이블은 유지) ----------


async def test_cascade_session_tags(del_db: aiosqlite.Connection) -> None:
    """session_tags 는 CASCADE 로 사라지고, tags 테이블은 그대로 유지."""
    await del_db.execute(
        "INSERT INTO tags(name, color, created_at) VALUES (?, ?, ?)",
        ("important", None, _ts()),
    )
    cur = await del_db.execute("SELECT tag_id FROM tags WHERE name='important'")
    tag_id = (await cur.fetchone())["tag_id"]
    await del_db.execute(
        "INSERT INTO session_tags(session_id, tag_id, tagged_at) VALUES (?, ?, ?)",
        ("session-del", tag_id, _ts()),
    )
    await del_db.commit()

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    cur = await del_db.execute(
        "SELECT COUNT(*) AS c FROM session_tags WHERE session_id = 'session-del'"
    )
    assert (await cur.fetchone())["c"] == 0

    # tags 행은 남아있어야 함
    cur = await del_db.execute("SELECT COUNT(*) AS c FROM tags WHERE name='important'")
    assert (await cur.fetchone())["c"] == 1


# ---------- 6. CASCADE notes ----------


async def test_cascade_notes(del_db: aiosqlite.Connection) -> None:
    """note 있는 세션 DELETE → notes 사라짐."""
    await del_db.execute(
        "INSERT INTO notes(session_id, body, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("session-del", "remember", _ts(), _ts()),
    )
    await del_db.commit()

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    cur = await del_db.execute("SELECT COUNT(*) AS c FROM notes WHERE session_id = 'session-del'")
    assert (await cur.fetchone())["c"] == 0


# ---------- 7. CASCADE highlights ----------


async def test_cascade_highlights(del_db: aiosqlite.Connection) -> None:
    """highlight 있는 세션 DELETE → highlights 사라짐."""
    await del_db.execute(
        "INSERT INTO highlights(session_id, message_uuid, text, kind, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("session-del", "u1", "notable", "insight", _ts()),
    )
    await del_db.commit()

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    cur = await del_db.execute(
        "SELECT COUNT(*) AS c FROM highlights WHERE session_id = 'session-del'"
    )
    assert (await cur.fetchone())["c"] == 0


# ---------- 8. CASCADE artifacts ----------


async def test_cascade_artifacts(del_db: aiosqlite.Connection) -> None:
    """artifact 있는 세션 DELETE → artifacts 사라짐."""
    await del_db.execute(
        "INSERT INTO artifacts(session_id, message_uuid, tool_name, path, created_at, indexed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("session-del", "u1", "Write", "/tmp/file.txt", _ts(), _ts()),
    )
    await del_db.commit()

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    cur = await del_db.execute(
        "SELECT COUNT(*) AS c FROM artifacts WHERE session_id = 'session-del'"
    )
    assert (await cur.fetchone())["c"] == 0


# ---------- 9. FTS 정리 ----------


async def test_fts_cleanup(del_db: aiosqlite.Connection) -> None:
    """DELETE 후 FTS5 인덱스에서도 세션이 제거 — search 쿼리에 안 나와야 함."""
    # 삭제 전: summary 가 있는 세션
    cur = await del_db.execute("SELECT summary FROM sessions WHERE session_id = 'session-del'")
    row = await cur.fetchone()
    summary = row["summary"] if row and row["summary"] else "delete me"

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    # FTS 검색으로 해당 세션이 안 나오면 OK — search_sessions 는 SearchResponse 반환
    response = await repo.search_sessions(del_db, query=summary, limit=10)
    ids = {item.session_id for item in response.items}
    assert "session-del" not in ids


# ---------- 10. ~/.claude/ 파일 무결성 ----------


async def test_claude_home_untouched(del_db: aiosqlite.Connection, del_settings: Settings) -> None:
    """DELETE 후 가짜 claude_home 의 jsonl 파일이 그대로 존재해야 함 (CLAUDE.md 제약 #1)."""
    jsonl_path = del_settings.paths.claude_home / "projects" / "-tmp-del-proj" / "session-del.jsonl"
    assert jsonl_path.is_file(), "전제 조건: 파일이 있어야 함"
    mtime_before = jsonl_path.stat().st_mtime

    await repo.delete_session(del_db, "session-del")
    await del_db.commit()

    # overlay 삭제 후에도 원본 jsonl 은 건재해야 함
    assert jsonl_path.is_file(), "DELETE 후에도 원본 jsonl 파일은 삭제되면 안 됨"
    assert jsonl_path.stat().st_mtime == mtime_before, "mtime 변경 없어야 함"
