"""Bootstrap (full) scan of ~/.claude/projects/ into the overlay DB."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from clave.models import ProjectRow, RescanResponse, SessionRow
from clave.overlay import repo
from clave.overlay.db import transaction
from clave.paths import cwd_exists, decode_project_id
from clave.scanner.aggregator import aggregate_jsonl

log = logging.getLogger(__name__)


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(timespec="seconds")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _count_subagent_files(session_dir: Path) -> int:
    sub = session_dir / "subagents"
    if not sub.is_dir():
        return 0
    return sum(1 for p in sub.glob("agent-*.jsonl"))


async def scan_project(
    conn: aiosqlite.Connection,
    project_dir: Path,
    *,
    only_session_id: str | None = None,
) -> tuple[int, int]:
    """Scan one project directory. Returns (scanned, skipped).

    Order matters: the project row is upserted first (so FK constraints on
    sessions.project_id are satisfied), then session rows.
    """
    project_id = project_dir.name

    jsonl_files = sorted(project_dir.glob("*.jsonl"))
    new_rows: list[SessionRow] = []
    skipped = 0
    sessions_started: list[str] = []
    sessions_last: list[str] = []
    cwd_hint: str | None = None

    # Phase 1: parse jsonls in memory (no DB writes), gather rollup info.
    for jp in jsonl_files:
        session_id = jp.stem
        if only_session_id and session_id != only_session_id:
            continue
        stat = jp.stat()
        size = stat.st_size
        mtime = _mtime_iso(jp)
        existing = await repo.get_session_signature(conn, session_id)
        if existing == (size, mtime):
            skipped += 1
            row = await repo.get_session(conn, session_id)
            if row:
                sessions_started.append(row.started_at)
                sessions_last.append(row.last_message_at)
                if cwd_hint is None and row.git_branch is None:
                    pass  # cwd hint only available from fresh parse
            continue

        summary = aggregate_jsonl(jp, session_id)
        if summary.message_count == 0:
            started = mtime
            last = mtime
        else:
            started = summary.started_at or mtime
            last = summary.last_message_at or mtime
        sessions_started.append(started)
        sessions_last.append(last)
        if cwd_hint is None and summary.cwd_from_user_msg:
            cwd_hint = summary.cwd_from_user_msg

        session_dir = project_dir / session_id
        sub_count = _count_subagent_files(session_dir)

        new_rows.append(
            SessionRow(
                session_id=session_id,
                project_id=project_id,
                jsonl_path=str(jp),
                started_at=started,
                last_message_at=last,
                message_count=summary.message_count,
                user_message_count=summary.user_message_count,
                assistant_message_count=summary.assistant_message_count,
                tool_use_count=summary.tool_use_count,
                subagent_count=sub_count,
                summary=summary.summary,
                git_branch=summary.git_branch,
                cc_version=summary.cc_version,
                file_size=size,
                file_mtime=mtime,
                indexed_at=_now_iso(),
            )
        )

    # Phase 2: write project + sessions atomically.
    decoded = cwd_hint or decode_project_id(project_id)
    if sessions_started:
        first_seen = min(sessions_started)
        last_active = max(sessions_last)
    else:
        dir_mtime = _mtime_iso(project_dir)
        first_seen = dir_mtime
        last_active = dir_mtime

    proj = ProjectRow(
        project_id=project_id,
        decoded_cwd=decoded,
        cwd_exists=cwd_exists(decoded),
        first_seen_at=first_seen,
        last_active_at=last_active,
        session_count=len(jsonl_files),
        indexed_at=_now_iso(),
    )

    async with transaction(conn):
        await repo.upsert_project(conn, proj)
        for row in new_rows:
            await repo.upsert_session(conn, row)

    return len(new_rows), skipped


async def run_full_scan(
    conn: aiosqlite.Connection,
    claude_home: Path,
    *,
    only_project_id: str | None = None,
) -> RescanResponse:
    """Scan all projects under <claude_home>/projects/."""
    projects_root = claude_home / "projects"
    started = time.perf_counter()
    if not projects_root.is_dir():
        log.warning("projects root does not exist: %s", projects_root)
        return RescanResponse(
            scanned_projects=0, scanned_sessions=0, skipped_sessions=0, elapsed_ms=0.0
        )

    scanned_p = 0
    scanned_s = 0
    skipped_s = 0
    for project_dir in sorted(p for p in projects_root.iterdir() if p.is_dir()):
        if only_project_id and project_dir.name != only_project_id:
            continue
        try:
            s, k = await scan_project(conn, project_dir)
        except Exception:
            log.exception("scan_project failed for %s", project_dir)
            continue
        scanned_p += 1
        scanned_s += s
        skipped_s += k

    elapsed_ms = (time.perf_counter() - started) * 1000
    return RescanResponse(
        scanned_projects=scanned_p,
        scanned_sessions=scanned_s,
        skipped_sessions=skipped_s,
        elapsed_ms=round(elapsed_ms, 2),
    )
