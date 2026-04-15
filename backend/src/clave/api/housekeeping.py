"""Housekeeping scan API — read-only, no writes to ~/.claude/."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import aiosqlite
from fastapi import APIRouter, Depends, Query, Request

from clave.api import get_db
from clave.models import HousekeepingCandidateItem, HousekeepingScanResponse
from clave.scanner.housekeeping import scan_candidates

router = APIRouter(prefix="/api", tags=["housekeeping"])


@router.get("/housekeeping/scan", response_model=HousekeepingScanResponse)
async def scan_endpoint(
    stale_days: int = Query(90, ge=1, le=3650),
    request: Request = None,  # type: ignore[assignment]
    db: aiosqlite.Connection = Depends(get_db),
) -> HousekeepingScanResponse:
    settings = request.app.state.settings
    cands = await scan_candidates(db, settings.paths.claude_home, stale_days=stale_days)

    summary: dict[str, int] = {}
    total = 0
    items: list[HousekeepingCandidateItem] = []
    for c in cands:
        summary[c.category] = summary.get(c.category, 0) + 1
        total += c.size_bytes or 0
        items.append(HousekeepingCandidateItem(**dataclasses.asdict(c)))

    return HousekeepingScanResponse(
        items=items,
        scanned_at=datetime.now(UTC).isoformat(timespec="seconds"),
        summary=summary,
        total_size_bytes=total,
    )
