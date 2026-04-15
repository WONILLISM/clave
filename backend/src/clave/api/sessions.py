from __future__ import annotations

from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from clave.api import get_db
from clave.models import SessionDetailResponse, SessionListResponse
from clave.overlay import repo
from clave.scanner.parser import iter_jsonl

router = APIRouter(prefix="/api", tags=["sessions"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions_endpoint(
    project_id: str | None = None,
    from_ts: str | None = Query(None, alias="from"),
    to_ts: str | None = Query(None, alias="to"),
    pinned: bool | None = None,
    tag: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> SessionListResponse:
    items, next_cursor = await repo.list_sessions(
        db,
        project_id=project_id,
        from_ts=from_ts,
        to_ts=to_ts,
        pinned=pinned,
        tag=tag,
        limit=limit,
        cursor=cursor,
    )
    return SessionListResponse(items=items, next_cursor=next_cursor)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_endpoint(
    session_id: str,
    offset: int = Query(0, ge=0, description="line offset to start from"),
    limit: int = Query(200, ge=1, le=2000),
    db: aiosqlite.Connection = Depends(get_db),
) -> SessionDetailResponse:
    meta = await repo.get_session_list_item(db, session_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="session not found")

    row = await repo.get_session(db, session_id)
    assert row is not None
    path = Path(row.jsonl_path)
    if not path.is_file():
        raise HTTPException(status_code=410, detail="session jsonl file is gone")

    messages = []
    seen = 0
    consumed = 0
    has_more = False
    for _raw, item in iter_jsonl(path):
        if seen < offset:
            seen += 1
            continue
        if consumed >= limit:
            has_more = True
            break
        messages.append(item)
        consumed += 1
        seen += 1

    return SessionDetailResponse(
        session=meta,
        messages=messages,
        has_more=has_more,
        next_offset=offset + consumed if has_more else offset + consumed,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session_endpoint(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> Response:
    """overlay DB 의 세션 흔적만 삭제. ~/.claude/ 는 절대 건드리지 않는다."""
    deleted = await repo.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="session not found")
    await db.commit()
    return Response(status_code=204)
