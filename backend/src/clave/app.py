"""FastAPI application factory + lifespan."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from clave.api import admin, housekeeping, knowledge, overlay, projects, search, sessions
from clave.config import Settings, load_settings
from clave.logging_setup import setup_logging
from clave.overlay.db import open_db
from clave.overlay.migrate import migrate
from clave.scanner.bootstrap import run_full_scan

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = load_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("clave starting; overlay=%s", settings.paths.overlay_db)
        conn = await open_db(settings.paths.overlay_db)
        version = await migrate(conn)
        log.info("schema version=%d", version)
        # Bootstrap scan on startup. Synchronous-await: small (~150 files).
        result = await run_full_scan(conn, settings.paths.claude_home)
        log.info(
            "bootstrap scan: projects=%d scanned=%d skipped=%d in %.1fms",
            result.scanned_projects,
            result.scanned_sessions,
            result.skipped_sessions,
            result.elapsed_ms,
        )
        app.state.db = conn
        app.state.settings = settings
        try:
            yield
        finally:
            await conn.close()
            log.info("clave shutting down")

    app = FastAPI(title="Clave", version="0.0.1", lifespan=lifespan)
    app.include_router(admin.router)
    app.include_router(projects.router)
    app.include_router(sessions.router)
    app.include_router(overlay.router)
    app.include_router(search.router)
    app.include_router(housekeeping.router)
    app.include_router(knowledge.router)
    return app


app = create_app()
