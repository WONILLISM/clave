"""Search endpoint — FTS5 over session summaries + file paths + project cwd."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Query

from clave.api import get_db
from clave.models import SearchResponse
from clave.overlay import repo

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: aiosqlite.Connection = Depends(get_db),
) -> SearchResponse:
    """FTS5 search across session summaries, file paths, and project paths."""
    return await repo.search_sessions(db, q, limit=limit)
