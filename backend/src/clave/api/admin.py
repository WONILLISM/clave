from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Request

from clave.api import get_db
from clave.models import HealthResponse, RescanRequest, RescanResponse
from clave.overlay import repo
from clave.scanner.bootstrap import run_full_scan

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/health", response_model=HealthResponse)
async def health_endpoint(
    request: Request, db: aiosqlite.Connection = Depends(get_db)
) -> HealthResponse:
    n = await repo.count_sessions(db)
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        db_path=str(settings.paths.overlay_db),
        indexed_sessions=n,
    )


@router.post("/admin/rescan", response_model=RescanResponse)
async def rescan_endpoint(
    body: RescanRequest | None = None,
    request: Request = None,  # type: ignore[assignment]
    db: aiosqlite.Connection = Depends(get_db),
) -> RescanResponse:
    settings = request.app.state.settings
    only = body.project_id if body else None
    return await run_full_scan(db, settings.paths.claude_home, only_project_id=only)
