from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Response, status

from clave.api import get_db
from clave.models import (
    AttachTagRequest,
    CreateNoteRequest,
    CreateTagRequest,
    NoteRow,
    TagListItem,
    TagRow,
    UpdateNoteRequest,
)
from clave.overlay import repo

router = APIRouter(prefix="/api", tags=["overlay"])


# ---------- Pins ----------


@router.post("/sessions/{session_id}/pin", status_code=status.HTTP_204_NO_CONTENT)
async def pin_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)) -> Response:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")
    await repo.add_pin(db, session_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/sessions/{session_id}/pin", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)) -> Response:
    await repo.remove_pin(db, session_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Tags ----------


@router.get("/tags", response_model=list[TagListItem])
async def list_tags_endpoint(db: aiosqlite.Connection = Depends(get_db)) -> list[TagListItem]:
    return await repo.list_tags(db)


@router.post("/tags", response_model=TagRow, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    body: CreateTagRequest, db: aiosqlite.Connection = Depends(get_db)
) -> TagRow:
    tag = await repo.create_tag(db, body.name, body.color)
    await db.commit()
    return tag


@router.post(
    "/sessions/{session_id}/tags", response_model=TagRow, status_code=status.HTTP_201_CREATED
)
async def attach_tag_endpoint(
    session_id: str,
    body: AttachTagRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> TagRow:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")

    if body.tag_id is None and not body.name:
        raise HTTPException(status_code=400, detail="provide tag_id or name")

    tag: TagRow | None
    if body.tag_id is not None:
        # look up by id
        cur = await db.execute("SELECT * FROM tags WHERE tag_id = ?", (body.tag_id,))
        r = await cur.fetchone()
        if r is None:
            raise HTTPException(status_code=404, detail="tag not found")
        tag = TagRow(**dict(r))
    else:
        assert body.name is not None
        tag = await repo.get_tag_by_name(db, body.name)
        if tag is None:
            tag = await repo.create_tag(db, body.name, None)
    await repo.attach_tag(db, session_id, tag.tag_id)
    await db.commit()
    return tag


@router.delete("/sessions/{session_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def detach_tag_endpoint(
    session_id: str, tag_id: int, db: aiosqlite.Connection = Depends(get_db)
) -> Response:
    await repo.detach_tag(db, session_id, tag_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Notes ----------


@router.get("/sessions/{session_id}/notes", response_model=list[NoteRow])
async def list_notes_endpoint(
    session_id: str, db: aiosqlite.Connection = Depends(get_db)
) -> list[NoteRow]:
    return await repo.list_notes(db, session_id)


@router.post(
    "/sessions/{session_id}/notes", response_model=NoteRow, status_code=status.HTTP_201_CREATED
)
async def create_note_endpoint(
    session_id: str,
    body: CreateNoteRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> NoteRow:
    if await repo.get_session(db, session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")
    note = await repo.create_note(db, session_id, body.body)
    await db.commit()
    return note


@router.patch("/notes/{note_id}", response_model=NoteRow)
async def update_note_endpoint(
    note_id: int,
    body: UpdateNoteRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> NoteRow:
    note = await repo.update_note(db, note_id, body.body)
    if note is None:
        raise HTTPException(status_code=404, detail="note not found")
    await db.commit()
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_endpoint(
    note_id: int, db: aiosqlite.Connection = Depends(get_db)
) -> Response:
    if not await repo.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="note not found")
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
