"""Housekeeping candidate detection — read-only scan of ~/.claude/.

Rules (MVP-0):
  1. stale_session  — no pin, no tags, last_message_at <= cutoff
  2. empty_project  — projects/<enc>/ has zero *.jsonl* files
  3. orphan_project — projects.decoded_cwd does not exist on the filesystem
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import aiosqlite

from clave.paths import cwd_exists

CategoryLiteral = Literal["stale_session", "empty_project", "orphan_project", "orphan_session"]


@dataclass
class Candidate:
    category: CategoryLiteral
    entity_id: str  # session_id | project_id
    display_name: str  # summary or cwd basename
    reason: str  # e.g. "마지막 메시지 118일 전, 핀/태그 없음"
    size_bytes: int | None = None
    last_activity: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


async def scan_candidates(
    conn: aiosqlite.Connection, claude_home: Path, *, stale_days: int = 90
) -> list[Candidate]:
    """Collect all housekeeping candidates and return sorted list."""
    out: list[Candidate] = []
    # orphan_session 먼저 — 더 강한 신호. stale_session 에서 중복 제외.
    orphan_results = await _orphan_sessions(conn)
    orphan_ids: set[str] = {c.entity_id for c in orphan_results}
    out += orphan_results
    out += await _stale_sessions(conn, stale_days=stale_days, exclude_ids=orphan_ids)
    # projects/ 부재 가드 — bootstrap.py 패턴 차용
    projects_root = claude_home / "projects"
    if projects_root.is_dir():
        out += await _empty_projects(conn, projects_root)
        out += await _orphan_projects(conn, projects_root)
    # size_bytes DESC (None 은 0 취급), tie-break: last_activity ASC
    out.sort(key=lambda c: (-(c.size_bytes or 0), c.last_activity or ""))
    return out


async def _stale_sessions(
    conn: aiosqlite.Connection,
    *,
    stale_days: int,
    exclude_ids: set[str] = set(),  # noqa: B006
) -> list[Candidate]:
    """pinned=False AND no tags AND last_message_at <= cutoff.

    exclude_ids: orphan_session 으로 이미 잡힌 session_id — 중복 제외.
    """
    cutoff = (datetime.now(UTC) - timedelta(days=stale_days)).isoformat(timespec="seconds")
    # overlay/repo.py list_sessions 필터 패턴 차용 — pins LEFT JOIN + session_tags NOT EXISTS
    base_sql = """
        SELECT s.session_id, s.summary, s.last_message_at, s.file_size
        FROM sessions s
        LEFT JOIN pins p ON p.session_id = s.session_id
        WHERE s.last_message_at <= ?
          AND p.session_id IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM session_tags st WHERE st.session_id = s.session_id
          )
    """
    params: list[object] = [cutoff]
    if exclude_ids:
        placeholders = ",".join("?" * len(exclude_ids))
        base_sql += f"\n          AND s.session_id NOT IN ({placeholders})"
        params.extend(exclude_ids)
    base_sql += "\n        ORDER BY s.last_message_at ASC"

    cur = await conn.execute(base_sql, params)
    rows = await cur.fetchall()
    return [
        Candidate(
            category="stale_session",
            entity_id=r["session_id"],
            display_name=r["summary"] or r["session_id"][:8],
            reason=f"마지막 메시지 {_days_since(r['last_message_at'])}일 전, 핀/태그 없음",
            size_bytes=r["file_size"],
            last_activity=r["last_message_at"],
            metadata={"stale_days_threshold": stale_days},
        )
        for r in rows
    ]


async def _orphan_sessions(conn: aiosqlite.Connection) -> list[Candidate]:
    """jsonl_path 가 실제 파일시스템에 없는 세션 탐지.

    핀/태그가 있으면 제외 (stale_session 과 동일 필터).
    size_bytes 는 None — 원본 파일 없으므로 측정 불가.
    """
    sql = """
        SELECT s.session_id, s.summary, s.last_message_at, s.jsonl_path
        FROM sessions s
        LEFT JOIN pins p ON p.session_id = s.session_id
        WHERE p.session_id IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM session_tags st WHERE st.session_id = s.session_id
          )
        ORDER BY s.last_message_at ASC
    """
    cur = await conn.execute(sql)
    rows = await cur.fetchall()

    candidates: list[Candidate] = []
    for r in rows:
        if Path(r["jsonl_path"]).is_file():
            continue
        candidates.append(
            Candidate(
                category="orphan_session",
                entity_id=r["session_id"],
                display_name=r["summary"] or r["session_id"][:8],
                reason="원본 jsonl 파일 사라짐",
                size_bytes=None,
                last_activity=r["last_message_at"],
                metadata={"jsonl_path": r["jsonl_path"]},
            )
        )
    return candidates


async def _empty_projects(conn: aiosqlite.Connection, projects_root: Path) -> list[Candidate]:
    """projects/<enc>/ 아래 .jsonl* 파일 0개인 프로젝트 탐지.

    glob("*.jsonl*") 로 .jsonl.gz 도 포함 — 압축 파일 오탐 방어.
    """
    # DB 에서 project_id 목록 조회
    cur = await conn.execute("SELECT project_id, decoded_cwd FROM projects")
    rows = await cur.fetchall()

    candidates: list[Candidate] = []
    for row in rows:
        project_dir = projects_root / row["project_id"]
        if not project_dir.is_dir():
            continue
        # *.jsonl* glob 으로 .jsonl 및 .jsonl.gz 모두 체크
        jsonl_files = list(project_dir.glob("*.jsonl*"))
        if jsonl_files:
            continue
        # 빈 프로젝트 — 디렉터리 전체 용량 계산 (to_thread: 이벤트 루프 블로킹 방지)
        size = await asyncio.to_thread(_dir_size_bytes, project_dir)
        cwd = row["decoded_cwd"]
        candidates.append(
            Candidate(
                category="empty_project",
                entity_id=row["project_id"],
                display_name=_basename(cwd),
                reason="세션 파일(.jsonl) 없음",
                size_bytes=size if size > 0 else None,
                last_activity=None,
                metadata={"decoded_cwd": cwd},
            )
        )
    return candidates


async def _orphan_projects(
    conn: aiosqlite.Connection,
    projects_root: Path,  # noqa: ARG001
) -> list[Candidate]:
    """projects.decoded_cwd 가 실제 파일시스템에 없는 프로젝트 탐지.

    paths.cwd_exists() 재사용 — os.path.exists 직접 호출 금지.
    projects_root 인자는 인터페이스 일관성을 위해 받지만 사용하지 않음.
    """
    cur = await conn.execute("SELECT project_id, decoded_cwd FROM projects")
    rows = await cur.fetchall()

    candidates: list[Candidate] = []
    for row in rows:
        decoded = row["decoded_cwd"]
        if cwd_exists(decoded):
            # cwd 살아있으면 고아 아님
            continue
        candidates.append(
            Candidate(
                category="orphan_project",
                entity_id=row["project_id"],
                display_name=_basename(decoded),
                reason=f"작업 디렉터리 없음: {decoded}",
                size_bytes=None,
                last_activity=None,
                metadata={"decoded_cwd": decoded},
            )
        )
    return candidates


def _days_since(iso: str) -> int:
    """ISO 8601 문자열로부터 경과 일 수 계산. 파싱 실패 시 -1 반환."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return -1  # 알 수 없으면 -1 (UI 에서 "?"로 표시 가능)
    return (datetime.now(UTC) - dt).days


def _dir_size_bytes(path: Path) -> int:
    """디렉터리 전체 파일 크기 합산 (rglob + stat — symlink 제외, 다른 fs 쓰기 연산 없음)."""
    return sum(f.stat().st_size for f in path.rglob("*") if not f.is_symlink() and f.is_file())


def _basename(path_str: str) -> str:
    """경로 문자열에서 마지막 세그먼트 반환."""
    idx = path_str.rstrip("/").rfind("/")
    return path_str[idx + 1 :] if idx >= 0 else path_str


__all__ = ["Candidate", "CategoryLiteral", "scan_candidates"]
