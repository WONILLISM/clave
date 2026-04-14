"""FastAPI dependency providing the shared aiosqlite connection."""

from __future__ import annotations

from collections.abc import AsyncIterator

import aiosqlite
from fastapi import Request


async def get_db(request: Request) -> AsyncIterator[aiosqlite.Connection]:
    conn: aiosqlite.Connection = request.app.state.db
    yield conn
