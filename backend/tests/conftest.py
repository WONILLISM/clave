"""Shared fixtures: build a fake ~/.claude/projects/ tree + isolated overlay DB."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from clave.app import create_app
from clave.config import PathsConfig, ScannerConfig, ServerConfig, Settings
from clave.overlay.db import open_db
from clave.overlay.migrate import migrate
from clave.scanner.bootstrap import run_full_scan


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


@pytest.fixture
def fake_claude_home(tmp_path: Path) -> Path:
    """Create a fake ~/.claude/ tree with two projects, three sessions."""
    claude_home = tmp_path / "claude"
    projects = claude_home / "projects"

    # Project A: encoded form of /tmp/proj-a (which doesn't exist)
    proj_a = projects / "-tmp-proj-a"
    _write_jsonl(
        proj_a / "session-aaa.jsonl",
        [
            {
                "type": "user",
                "uuid": "u1",
                "timestamp": "2026-04-10T10:00:00.000Z",
                "sessionId": "session-aaa",
                "cwd": "/tmp/proj-a",
                "version": "2.1.92",
                "gitBranch": "main",
                "message": {"role": "user", "content": "Hello world"},
            },
            {
                "type": "assistant",
                "uuid": "a1",
                "timestamp": "2026-04-10T10:00:05.000Z",
                "sessionId": "session-aaa",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Hi"},
                        {"type": "tool_use", "id": "t1", "name": "Read", "input": {"x": 1}},
                    ],
                },
            },
            "this line is broken json",  # invalid
            {
                "type": "queue-operation",
                "operation": "enqueue",
                "timestamp": "2026-04-10T10:00:10.000Z",
            },
        ],
    )
    _write_jsonl(
        proj_a / "session-bbb.jsonl",
        [
            {
                "type": "user",
                "uuid": "u2",
                "timestamp": "2026-04-12T09:00:00.000Z",
                "sessionId": "session-bbb",
                "cwd": "/tmp/proj-a",
                "message": {"role": "user", "content": "Second session"},
            }
        ],
    )

    # Project B: empty jsonl + a real cwd that exists (use tmp_path itself)
    proj_b_encoded = str(tmp_path).replace("/", "-")  # e.g. -private-var-folders-...
    proj_b = projects / proj_b_encoded
    _write_jsonl(
        proj_b / "session-ccc.jsonl",
        [
            {
                "type": "user",
                "uuid": "u3",
                "timestamp": "2026-04-13T08:00:00.000Z",
                "sessionId": "session-ccc",
                "cwd": str(tmp_path),
                "message": {"role": "user", "content": "Third"},
            }
        ],
    )

    return claude_home


@pytest.fixture
def settings(tmp_path: Path, fake_claude_home: Path) -> Settings:
    return Settings(
        paths=PathsConfig(
            claude_home=fake_claude_home,
            overlay_db=tmp_path / "overlay.sqlite",
            trash_dir=tmp_path / "trash",
        ),
        server=ServerConfig(),
        scanner=ScannerConfig(),
    )


@pytest_asyncio.fixture
async def db(settings: Settings) -> AsyncIterator[aiosqlite.Connection]:
    conn = await open_db(settings.paths.overlay_db)
    await migrate(conn)
    try:
        yield conn
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def db_scanned(db: aiosqlite.Connection, settings: Settings) -> aiosqlite.Connection:
    await run_full_scan(db, settings.paths.claude_home)
    return db


@pytest_asyncio.fixture
async def client(settings: Settings):
    """Spin up the FastAPI app with our test settings."""
    from httpx import ASGITransport, AsyncClient

    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
