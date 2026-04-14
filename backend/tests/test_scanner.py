from __future__ import annotations

import aiosqlite

from clave.config import Settings
from clave.overlay import repo
from clave.scanner.bootstrap import run_full_scan


async def test_full_scan_indexes_expected_rows(
    db: aiosqlite.Connection, settings: Settings
) -> None:
    result = await run_full_scan(db, settings.paths.claude_home)
    assert result.scanned_projects == 2
    assert result.scanned_sessions == 3
    assert result.skipped_sessions == 0
    assert await repo.count_sessions(db) == 3

    projects = await repo.list_projects(db)
    assert len(projects) == 2

    s = await repo.get_session(db, "session-aaa")
    assert s is not None
    assert s.user_message_count == 1
    assert s.assistant_message_count == 1
    assert s.tool_use_count == 1
    assert s.summary == "Hello world"
    assert s.git_branch == "main"


async def test_incremental_scan_skips_unchanged(
    db: aiosqlite.Connection, settings: Settings
) -> None:
    await run_full_scan(db, settings.paths.claude_home)
    second = await run_full_scan(db, settings.paths.claude_home)
    assert second.scanned_sessions == 0
    assert second.skipped_sessions == 3
