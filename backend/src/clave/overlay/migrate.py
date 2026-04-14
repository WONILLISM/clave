"""Tiny SQL migrator. Reads migrations/*.sql, applies sequentially."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

MIGRATION_RE = re.compile(r"^(\d{4})_.*\.sql$")


def _migrations_dir() -> Path:
    # backend/src/clave/overlay/migrate.py -> backend/migrations/
    return Path(__file__).resolve().parents[3] / "migrations"


def _discover() -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for p in sorted(_migrations_dir().glob("*.sql")):
        m = MIGRATION_RE.match(p.name)
        if not m:
            continue
        out.append((int(m.group(1)), p))
    return out


async def _current_version(conn: aiosqlite.Connection) -> int:
    cur = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if not await cur.fetchone():
        return 0
    cur = await conn.execute("SELECT MAX(version) FROM schema_version")
    row = await cur.fetchone()
    return int(row[0] or 0)


async def migrate(conn: aiosqlite.Connection) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    current = await _current_version(conn)
    pending = [(v, p) for v, p in _discover() if v > current]
    if not pending:
        return current
    for _version, path in pending:
        log.info("applying migration %s", path.name)
        sql = path.read_text(encoding="utf-8")
        await conn.executescript(sql)
        await conn.commit()
    return await _current_version(conn)
