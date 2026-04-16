"""Knowledge Graph API — CRUD + links + promote."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from clave.api import get_db
from clave.models import (
    CreateKnowledgeRequest,
    CreateLinkRequest,
    KnowledgeDetailResponse,
    KnowledgeLinkRow,
    KnowledgeListResponse,
    KnowledgeRow,
    PromoteHighlightRequest,
    UpdateKnowledgeRequest,
)
from clave.overlay import repo

router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge_endpoint(
    kind: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeListResponse:
    if q:
        items = await repo.search_knowledge(db, q, limit=limit)
        return KnowledgeListResponse(items=items, total_count=len(items))
    items, total = await repo.list_knowledge(db, kind=kind, limit=limit, offset=offset)
    next_off = offset + limit if offset + limit < total else None
    return KnowledgeListResponse(items=items, total_count=total, next_offset=next_off)


@router.post("/knowledge", response_model=KnowledgeRow, status_code=201)
async def create_knowledge_endpoint(
    req: CreateKnowledgeRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeRow:
    ki = await repo.create_knowledge(
        db,
        title=req.title,
        body=req.body,
        kind=req.kind,
        source_type=req.source_type,
        source_id=req.source_id,
    )
    await db.commit()
    return ki


@router.get("/knowledge/{knowledge_id}", response_model=KnowledgeDetailResponse)
async def get_knowledge_endpoint(
    knowledge_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeDetailResponse:
    ki = await repo.get_knowledge(db, knowledge_id)
    if ki is None:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    links = await repo.list_links(db, "knowledge", str(knowledge_id))
    backlinks = await repo.list_backlinks(db, "knowledge", str(knowledge_id))
    return KnowledgeDetailResponse(item=ki, links=links, backlinks=backlinks)


@router.patch("/knowledge/{knowledge_id}", response_model=KnowledgeRow)
async def update_knowledge_endpoint(
    knowledge_id: int,
    req: UpdateKnowledgeRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeRow:
    ki = await repo.update_knowledge(
        db,
        knowledge_id,
        title=req.title,
        body=req.body,
        kind=req.kind,
    )
    if ki is None:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    await db.commit()
    return ki


@router.delete("/knowledge/{knowledge_id}", status_code=204)
async def delete_knowledge_endpoint(
    knowledge_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> Response:
    deleted = await repo.delete_knowledge(db, knowledge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    await db.commit()
    return Response(status_code=204)


@router.post("/knowledge/{knowledge_id}/links", response_model=KnowledgeLinkRow, status_code=201)
async def create_link_endpoint(
    knowledge_id: int,
    req: CreateLinkRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeLinkRow:
    # Ensure the knowledge item exists.
    ki = await repo.get_knowledge(db, knowledge_id)
    if ki is None:
        raise HTTPException(status_code=404, detail="knowledge item not found")
    link = await repo.create_link(
        db,
        from_type=req.from_type,
        from_id=req.from_id,
        to_type=req.to_type,
        to_id=req.to_id,
        relation=req.relation,
    )
    if link is None:
        raise HTTPException(status_code=500, detail="failed to create link")
    await db.commit()
    return link


@router.delete("/knowledge/links/{link_id}", status_code=204)
async def delete_link_endpoint(
    link_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> Response:
    deleted = await repo.delete_link(db, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="link not found")
    await db.commit()
    return Response(status_code=204)


@router.post("/knowledge/from-highlight", response_model=KnowledgeRow, status_code=201)
async def promote_highlight_endpoint(
    req: PromoteHighlightRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> KnowledgeRow:
    ki = await repo.promote_highlight_to_knowledge(
        db,
        highlight_id=req.highlight_id,
        title=req.title,
        kind=req.kind,
    )
    if ki is None:
        raise HTTPException(status_code=404, detail="highlight not found")
    await db.commit()
    return ki
