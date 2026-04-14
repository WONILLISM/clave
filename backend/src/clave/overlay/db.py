"""SQLite connection helpers (aiosqlite + WAL)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


async def open_db(path: Path) -> aiosqlite.Connection:
    """Open an aiosqlite connection with WAL + foreign keys enabled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.execute("PRAGMA busy_timeout=5000")
    return conn


@asynccontextmanager
async def transaction(conn: aiosqlite.Connection) -> AsyncIterator[aiosqlite.Connection]:
    """Explicit transaction wrapper. aiosqlite is in autocommit-ish mode by default."""
    await conn.execute("BEGIN")
    try:
        yield conn
    except Exception:
        await conn.rollback()
        raise
    else:
        await conn.commit()
