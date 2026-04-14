from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends

from clave.api import get_db
from clave.models import ProjectListItem
from clave.overlay import repo

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=list[ProjectListItem])
async def list_projects_endpoint(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ProjectListItem]:
    return await repo.list_projects(db)
