"""Artifact 스캐너 + path-grouped 카탈로그 통합 테스트.

aggregator → bootstrap → repo 전 구간. ArtifactsPanel·이벤트 로그 엔드포인트를
W4.5-A 에서 제거하면서 repo API 가 path 중심으로 재설계됨.
"""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from clave.config import PathsConfig, ScannerConfig, ServerConfig, Settings
from clave.overlay import repo
from clave.overlay.db import open_db
from clave.overlay.migrate import migrate
from clave.scanner.bootstrap import run_full_scan


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


@pytest.fixture
def artifact_claude_home(tmp_path: Path) -> Path:
    """두 세션이 같은 파일(a.md)과 서로 다른 파일(b.md)을 다양한 tool 로 건드리는 fake tree."""
    claude_home = tmp_path / "claude"
    proj = claude_home / "projects" / "-tmp-proj-art"

    # 세션 1: a.md 를 Write + Edit. Read 는 인덱싱 제외 대상.
    _write_jsonl(
        proj / "session-one.jsonl",
        [
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-04-15T10:00:00.000Z",
                "sessionId": "session-one",
                "cwd": "/tmp/proj-art",
                "message": {"role": "user", "content": "first"},
            },
            {
                "type": "assistant",
                "uuid": "a1",
                "timestamp": "2026-04-15T10:00:05.000Z",
                "sessionId": "session-one",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "t1",
                            "name": "Write",
                            "input": {"file_path": "/tmp/art/a.md", "content": "x"},
                        },
                        {
                            "type": "tool_use",
                            "id": "t2",
                            "name": "Read",
                            "input": {"file_path": "/tmp/art/ref.md"},
                        },
                    ],
                },
            },
            {
                "type": "assistant",
                "uuid": "a2",
                "timestamp": "2026-04-15T10:00:10.000Z",
                "sessionId": "session-one",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "t3",
                            "name": "Edit",
                            "input": {
                                "file_path": "/tmp/art/a.md",
                                "old_string": "x",
                                "new_string": "y",
                            },
                        },
                    ],
                },
            },
        ],
    )

    # 세션 2: 같은 a.md 를 MultiEdit 로 다시 건드림 + 별도 파일 b.md Write. 더 늦은 시각.
    _write_jsonl(
        proj / "session-two.jsonl",
        [
            {
                "type": "user",
                "uuid": "u3",
                "timestamp": "2026-04-15T11:00:00.000Z",
                "sessionId": "session-two",
                "cwd": "/tmp/proj-art",
                "message": {"role": "user", "content": "second"},
            },
            {
                "type": "assistant",
                "uuid": "a3",
                "timestamp": "2026-04-15T11:00:05.000Z",
                "sessionId": "session-two",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "t4",
                            "name": "MultiEdit",
                            "input": {
                                "file_path": "/tmp/art/a.md",
                                "edits": [],
                            },
                        },
                        {
                            "type": "tool_use",
                            "id": "t5",
                            "name": "Write",
                            "input": {"file_path": "/tmp/art/b.md", "content": "z"},
                        },
                    ],
                },
            },
        ],
    )
    return claude_home


@pytest.fixture
def artifact_settings(tmp_path: Path, artifact_claude_home: Path) -> Settings:
    return Settings(
        paths=PathsConfig(
            claude_home=artifact_claude_home,
            overlay_db=tmp_path / "overlay.sqlite",
            trash_dir=tmp_path / "trash",
        ),
        server=ServerConfig(),
        scanner=ScannerConfig(),
    )


@pytest_asyncio.fixture
async def artifact_db(artifact_settings: Settings):
    conn = await open_db(artifact_settings.paths.overlay_db)
    await migrate(conn)
    try:
        yield conn
    finally:
        await conn.close()


# ---------- Scanner: 이벤트 로그가 DB 에 제대로 쌓이는지 (raw SQL 확인) ----------


async def test_bootstrap_inserts_artifact_events(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """Write/Edit/MultiEdit 이벤트는 그대로 행으로 인덱싱, Read 는 제외.

    a.md 는 session-one 에서 2건(Write, Edit) + session-two 에서 1건(MultiEdit) = 3건.
    b.md 는 session-two 에서 1건(Write).
    """
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    cur = await artifact_db.execute(
        "SELECT path, tool_name, session_id FROM artifacts ORDER BY created_at ASC"
    )
    rows = await cur.fetchall()
    assert len(rows) == 4
    assert [(r["path"], r["tool_name"]) for r in rows] == [
        ("/tmp/art/a.md", "Write"),
        ("/tmp/art/a.md", "Edit"),
        ("/tmp/art/a.md", "MultiEdit"),
        ("/tmp/art/b.md", "Write"),
    ]


async def test_rescan_is_idempotent(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """같은 jsonl 재스캔해도 행 수는 동일 (delete-then-insert)."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)
    cur = await artifact_db.execute("SELECT COUNT(*) AS c FROM artifacts")
    before = (await cur.fetchone())["c"]

    # signature 무효화해서 강제 재파싱
    await artifact_db.execute("UPDATE sessions SET file_size = -1")
    await artifact_db.commit()

    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)
    cur = await artifact_db.execute("SELECT COUNT(*) AS c FROM artifacts")
    after = (await cur.fetchone())["c"]

    assert before == after == 4


# ---------- list_artifact_paths: 1 path = 1 행 카탈로그 ----------


async def test_list_paths_groups_by_path(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """같은 path 를 여러 세션이 여러 번 건드려도 1행. edit_count·session_count 집계 검증."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    items = await repo.list_artifact_paths(artifact_db, limit=10)
    assert len(items) == 2  # a.md, b.md

    a = next(i for i in items if i.path == "/tmp/art/a.md")
    assert a.edit_count == 3
    assert a.session_count == 2
    # GROUP_CONCAT(DISTINCT) 의 결과는 정렬되어야 함 (repo 에서 sorted 적용)
    assert a.tools == ["Edit", "MultiEdit", "Write"]
    # 마지막 수정은 session-two (더 늦은 시각)
    assert a.last_session_id == "session-two"
    assert a.last_session_summary == "second"

    b = next(i for i in items if i.path == "/tmp/art/b.md")
    assert b.edit_count == 1
    assert b.session_count == 1
    assert b.tools == ["Write"]
    assert b.last_session_id == "session-two"


async def test_list_paths_last_modified_desc(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """최근 수정순 DESC 정렬. a.md, b.md 모두 session-two 에서 마지막 수정됐지만,
    b.md 는 session-two 안에서 a.md MultiEdit 와 같은 메시지라 created_at 동일."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    items = await repo.list_artifact_paths(artifact_db, limit=10)
    timestamps = [i.last_modified for i in items]
    assert timestamps == sorted(timestamps, reverse=True)


async def test_list_paths_search(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    items = await repo.list_artifact_paths(artifact_db, path_contains="b.md")
    assert len(items) == 1
    assert items[0].path == "/tmp/art/b.md"


async def test_list_paths_pagination(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    page1 = await repo.list_artifact_paths(artifact_db, limit=1, offset=0)
    page2 = await repo.list_artifact_paths(artifact_db, limit=1, offset=1)
    assert len(page1) == 1 and len(page2) == 1
    assert page1[0].path != page2[0].path


# ---------- list_sessions_for_artifact_path: path → 세션 역참조 ----------


async def test_list_sessions_for_path(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    sessions = await repo.list_sessions_for_artifact_path(artifact_db, "/tmp/art/a.md")
    assert len(sessions) == 2
    # MAX(created_at) DESC 정렬 — session-two 가 먼저
    assert sessions[0].session_id == "session-two"
    assert sessions[1].session_id == "session-one"

    # session-one 은 Write + Edit 2건 → edit_count=2, 마지막 tool 은 Edit
    s_one = sessions[1]
    assert s_one.edit_count == 2
    assert s_one.tool_name == "Edit"
    assert s_one.message_uuid == "a2"
    assert s_one.decoded_cwd == "/tmp/proj-art"
    assert s_one.session_summary == "first"


async def test_sessions_for_missing_path_empty(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    sessions = await repo.list_sessions_for_artifact_path(artifact_db, "/tmp/art/does-not-exist.md")
    assert sessions == []


async def test_cascade_on_session_delete(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """FK CASCADE — session 행 삭제 시 artifact 도 함께 사라짐."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    await artifact_db.execute("DELETE FROM sessions WHERE session_id = 'session-two'")
    await artifact_db.commit()

    cur = await artifact_db.execute("SELECT COUNT(*) AS c FROM artifacts")
    assert (await cur.fetchone())["c"] == 2  # session-one 의 Write + Edit 만 남음

    items = await repo.list_artifact_paths(artifact_db, limit=10)
    # b.md 는 session-two 에만 있었으므로 사라짐
    assert {i.path for i in items} == {"/tmp/art/a.md"}
