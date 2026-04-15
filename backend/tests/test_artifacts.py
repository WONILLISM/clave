"""Artifact 스캐너 통합 테스트.

conftest 의 fake tree 는 Read/queue 만 사용하므로 artifact 가 0 이라 별도 fake 를 만든다.
aggregator → bootstrap → repo → API 전 구간 통과를 한 번에 확인.
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
    """Write/Edit/Read 가 섞인 한 세션짜리 fake tree."""
    claude_home = tmp_path / "claude"
    proj = claude_home / "projects" / "-tmp-proj-art"
    _write_jsonl(
        proj / "session-art.jsonl",
        [
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-04-15T10:00:00.000Z",
                "sessionId": "session-art",
                "cwd": "/tmp/proj-art",
                "message": {"role": "user", "content": "do stuff"},
            },
            {
                "type": "assistant",
                "uuid": "a1",
                "timestamp": "2026-04-15T10:00:05.000Z",
                "sessionId": "session-art",
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
                "sessionId": "session-art",
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


async def test_bootstrap_inserts_artifacts(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """Write/Edit 로 만든 파일 2건이 artifact 로 인덱싱되고 Read 는 제외되는지."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    rows = await repo.list_artifacts_for_session(artifact_db, "session-art")
    # a.md 를 Write 1번 + Edit 1번 = 2행. /tmp/art/ref.md 의 Read 는 제외.
    assert len(rows) == 2
    tools = sorted(r.tool_name for r in rows)
    assert tools == ["Edit", "Write"]
    assert all(r.path == "/tmp/art/a.md" for r in rows)
    # message_uuid 가 tool_use 가 속한 assistant message uuid 로 채워짐
    assert {r.message_uuid for r in rows} == {"a1", "a2"}
    # created_at 은 message timestamp
    assert sorted(r.created_at for r in rows) == [
        "2026-04-15T10:00:05.000Z",
        "2026-04-15T10:00:10.000Z",
    ]


async def test_rescan_is_idempotent(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    """같은 jsonl 로 재스캔해도 artifact 행은 2개로 유지 (delete-then-insert)."""
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)
    first = await repo.list_artifacts_for_session(artifact_db, "session-art")

    # signature 무효화해서 강제 재파싱
    await artifact_db.execute("UPDATE sessions SET file_size = -1")
    await artifact_db.commit()

    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)
    second = await repo.list_artifacts_for_session(artifact_db, "session-art")

    assert len(first) == len(second) == 2


async def test_list_all_artifacts_joins_session_summary(
    artifact_db: aiosqlite.Connection, artifact_settings: Settings
) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    items = await repo.list_all_artifacts(artifact_db, limit=10)
    assert len(items) == 2
    # summary = 첫 user 메시지 "do stuff"
    assert items[0].session_summary == "do stuff"
    assert items[0].session_decoded_cwd == "/tmp/proj-art"


async def test_tool_filter(artifact_db: aiosqlite.Connection, artifact_settings: Settings) -> None:
    await run_full_scan(artifact_db, artifact_settings.paths.claude_home)

    writes = await repo.list_all_artifacts(artifact_db, tool_filter="Write")
    assert len(writes) == 1
    assert writes[0].tool_name == "Write"

    edits = await repo.list_all_artifacts(artifact_db, tool_filter="Edit")
    assert len(edits) == 1
    assert edits[0].tool_name == "Edit"
