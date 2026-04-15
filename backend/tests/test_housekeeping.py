"""Housekeeping candidate detection — 단위 + 통합 테스트.

scan_candidates() 의 3개 룰(stale_session / empty_project / orphan_project),
정렬, summary dict 키·값, 엣지 케이스(projects/ 미존재, Z suffix timezone 등)를 검증한다.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio

from clave.config import PathsConfig, ScannerConfig, ServerConfig, Settings
from clave.overlay.db import open_db
from clave.overlay.migrate import migrate
from clave.scanner.bootstrap import run_full_scan
from clave.scanner.housekeeping import _days_since, scan_candidates

# ---------- 헬퍼 ----------


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _ts(days_ago: int) -> str:
    """UTC 기준 N일 전 ISO 8601 timestamp (Z suffix)."""
    dt = datetime.now(UTC) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _user_msg(session_id: str, cwd: str, days_ago: int, content: str = "msg") -> dict:
    return {
        "type": "user",
        "uuid": f"u-{session_id}",
        "timestamp": _ts(days_ago),
        "sessionId": session_id,
        "cwd": cwd,
        "message": {"role": "user", "content": content},
    }


# ---------- Fixtures ----------


@pytest.fixture
def hk_claude_home(tmp_path: Path) -> Path:
    """세션 4개 + 프로젝트 3개로 구성된 fake claude_home."""
    claude_home = tmp_path / "claude"
    projects = claude_home / "projects"

    # 프로젝트 A: cwd=/tmp/stale-proj (실존하지 않음)
    # - session-stale: 100일 전, 핀/태그 없음 → stale_session 후보
    # - session-recent: 30일 전, 핀/태그 없음 → 제외 (stale_days=90 기준)
    _write_jsonl(
        projects / "-tmp-stale-proj" / "session-stale.jsonl",
        [_user_msg("session-stale", "/tmp/stale-proj", 100, "old work")],
    )
    _write_jsonl(
        projects / "-tmp-stale-proj" / "session-recent.jsonl",
        [_user_msg("session-recent", "/tmp/stale-proj", 30, "recent work")],
    )

    # 프로젝트 B: cwd=tmp_path (실존) — jsonl 없음 → empty_project 후보
    # (orphan은 아님: cwd 실존)
    (projects / "-tmp-empty-proj").mkdir(parents=True, exist_ok=True)

    # 프로젝트 C: cwd=/nonexistent/path (실존하지 않음), jsonl 있음 → orphan_project 후보
    _write_jsonl(
        projects / "-nonexistent-path" / "session-orphan.jsonl",
        [_user_msg("session-orphan", "/nonexistent/path", 200, "orphan session")],
    )

    return claude_home


@pytest.fixture
def hk_settings(tmp_path: Path, hk_claude_home: Path) -> Settings:
    return Settings(
        paths=PathsConfig(
            claude_home=hk_claude_home,
            overlay_db=tmp_path / "hk-overlay.sqlite",
            trash_dir=tmp_path / "trash",
        ),
        server=ServerConfig(),
        scanner=ScannerConfig(),
    )


@pytest_asyncio.fixture
async def hk_db(hk_settings: Settings) -> aiosqlite.Connection:
    conn = await open_db(hk_settings.paths.overlay_db)
    await migrate(conn)
    await run_full_scan(conn, hk_settings.paths.claude_home)
    try:
        yield conn
    finally:
        await conn.close()


# ---------- 1. stale_session 탐지 ----------


async def test_detect_stale_sessions(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """100일 전 세션 + 핀/태그 없음 → 후보 포함. days_since 계산이 100±2 범위."""
    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    stale = [c for c in cands if c.category == "stale_session"]

    ids = {c.entity_id for c in stale}
    assert "session-stale" in ids

    stale_cand = next(c for c in stale if c.entity_id == "session-stale")
    assert stale_cand.last_activity is not None
    days = _days_since(stale_cand.last_activity)
    assert 98 <= days <= 102, f"예상 100±2, 실제 {days}"


# ---------- 2. pinned 제외 ----------


async def test_pinned_excluded(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """pins 테이블에 등록된 세션은 stale_session 후보에서 제외."""
    await hk_db.execute(
        "INSERT INTO pins(session_id, pinned_at) VALUES (?, ?)",
        ("session-stale", datetime.now(UTC).isoformat(timespec="seconds")),
    )
    await hk_db.commit()

    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    stale_ids = {c.entity_id for c in cands if c.category == "stale_session"}
    assert "session-stale" not in stale_ids


# ---------- 3. tagged 제외 ----------


async def test_tagged_excluded(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """tags + session_tags INSERT 한 세션은 stale_session 후보에서 제외."""
    await hk_db.execute(
        "INSERT INTO tags(name, color, created_at) VALUES (?, ?, ?)",
        ("keep", None, datetime.now(UTC).isoformat(timespec="seconds")),
    )
    cur = await hk_db.execute("SELECT tag_id FROM tags WHERE name='keep'")
    tag_id = (await cur.fetchone())["tag_id"]

    await hk_db.execute(
        "INSERT INTO session_tags(session_id, tag_id, tagged_at) VALUES (?, ?, ?)",
        ("session-stale", tag_id, datetime.now(UTC).isoformat(timespec="seconds")),
    )
    await hk_db.commit()

    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    stale_ids = {c.entity_id for c in cands if c.category == "stale_session"}
    assert "session-stale" not in stale_ids


# ---------- 4. 최근 세션 제외 ----------


async def test_recent_not_stale(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """stale_days=90 기준 30일 전 세션은 stale_session 후보 아님."""
    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    stale_ids = {c.entity_id for c in cands if c.category == "stale_session"}
    assert "session-recent" not in stale_ids


# ---------- 5. 빈 프로젝트 탐지 ----------


async def test_empty_project_detected(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """projects/<enc>/ 디렉터리가 존재하고 .jsonl* 0개 → empty_project 후보."""
    # -tmp-empty-proj 는 프로젝트 디렉터리만 있고 jsonl 없음
    # 단, DB에 project 행이 있어야 하므로 직접 INSERT
    await hk_db.execute(
        """INSERT OR IGNORE INTO projects
           (project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            "-tmp-empty-proj",
            "/tmp/empty-proj",
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
            datetime.now(UTC).isoformat(timespec="seconds"),
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
        ),
    )
    await hk_db.commit()

    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    empty_ids = {c.entity_id for c in cands if c.category == "empty_project"}
    assert "-tmp-empty-proj" in empty_ids


# ---------- 6. jsonl 있으면 빈 프로젝트 아님 ----------


async def test_project_with_jsonl_not_empty(tmp_path: Path) -> None:
    """*.jsonl 파일이 1개 이상이면 empty_project 후보 아님."""
    claude_home = tmp_path / "claude"
    proj_dir = claude_home / "projects" / "-tmp-has-jsonl"
    _write_jsonl(
        proj_dir / "session-x.jsonl",
        [_user_msg("session-x", "/tmp/has-jsonl", 200)],
    )

    overlay_db = tmp_path / "test.sqlite"
    conn = await open_db(overlay_db)
    await migrate(conn)
    await run_full_scan(conn, claude_home)

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    empty_ids = {c.entity_id for c in cands if c.category == "empty_project"}
    assert "-tmp-has-jsonl" not in empty_ids
    await conn.close()


# ---------- 7. .jsonl.gz 있으면 빈 프로젝트 아님 ----------


async def test_project_with_jsonl_gz_not_empty(tmp_path: Path) -> None:
    """.jsonl.gz 만 있어도 *.jsonl* glob 에 매칭 → empty_project 후보 아님."""
    claude_home = tmp_path / "claude"
    proj_dir = claude_home / "projects" / "-tmp-has-gz"
    proj_dir.mkdir(parents=True, exist_ok=True)
    # .jsonl.gz 파일 생성 (내용 무관)
    (proj_dir / "session-y.jsonl.gz").write_bytes(b"\x1f\x8b")

    overlay_db = tmp_path / "test.sqlite"
    conn = await open_db(overlay_db)
    await migrate(conn)

    # DB에 project 행 INSERT (bootstrap은 .jsonl.gz 파싱 안 함)
    await conn.execute(
        """INSERT OR IGNORE INTO projects
           (project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            "-tmp-has-gz",
            "/tmp/has-gz",
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
            datetime.now(UTC).isoformat(timespec="seconds"),
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
        ),
    )
    await conn.commit()

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    empty_ids = {c.entity_id for c in cands if c.category == "empty_project"}
    assert "-tmp-has-gz" not in empty_ids
    await conn.close()


# ---------- 8. 고아 프로젝트 탐지 ----------


async def test_orphan_project_when_cwd_missing(
    hk_db: aiosqlite.Connection, hk_settings: Settings
) -> None:
    """decoded_cwd 가 실제 파일시스템에 없으면 orphan_project 후보."""
    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)
    orphan_cwds = {c.metadata.get("decoded_cwd") for c in cands if c.category == "orphan_project"}
    assert "/nonexistent/path" in orphan_cwds


# ---------- 9. 실존 cwd 는 고아 아님 ----------


async def test_existing_cwd_not_orphan(tmp_path: Path) -> None:
    """tmp_path 안에 실존 디렉터리를 cwd 로 설정하면 orphan_project 아님."""
    claude_home = tmp_path / "claude"
    real_cwd = tmp_path / "real-project"
    real_cwd.mkdir(parents=True, exist_ok=True)

    # real_cwd 를 인코딩한 project_id
    proj_id = str(real_cwd).replace("/", "-")
    proj_dir = claude_home / "projects" / proj_id
    _write_jsonl(
        proj_dir / "session-real.jsonl",
        [_user_msg("session-real", str(real_cwd), 200)],
    )

    overlay_db = tmp_path / "test.sqlite"
    conn = await open_db(overlay_db)
    await migrate(conn)
    await run_full_scan(conn, claude_home)

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan_ids = {c.entity_id for c in cands if c.category == "orphan_project"}
    assert proj_id not in orphan_ids
    await conn.close()


# ---------- 10. projects/ 디렉터리 자체 없을 때 예외 없음 ----------


async def test_no_projects_dir(tmp_path: Path) -> None:
    """claude_home/projects/ 자체가 없을 때 stale_session 만 반환하고 예외 없음."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)
    # projects/ 디렉터리를 생성하지 않음

    overlay_db = tmp_path / "test.sqlite"
    conn = await open_db(overlay_db)
    await migrate(conn)

    # stale 세션 직접 INSERT — jsonl 파일은 실제로 생성해야 orphan_session 으로 오탐 안 됨
    now = datetime.now(UTC)
    stale_ts = (now - timedelta(days=100)).isoformat(timespec="seconds")
    fake_jsonl = tmp_path / "s-nodir.jsonl"
    fake_jsonl.write_text("{}\n")
    await conn.execute(
        """INSERT INTO projects(project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("-tmp-no-dir", "/tmp/no-dir", 0, stale_ts, stale_ts, 1, stale_ts),
    )
    await conn.execute(
        """INSERT INTO sessions(session_id, project_id, jsonl_path, started_at, last_message_at,
                                message_count, user_message_count, assistant_message_count,
                                tool_use_count, subagent_count, file_size, file_mtime, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "s-nodir",
            "-tmp-no-dir",
            str(fake_jsonl),
            stale_ts,
            stale_ts,
            1,
            1,
            0,
            0,
            0,
            100,
            stale_ts,
            stale_ts,
        ),
    )
    await conn.commit()

    # 예외 없이 실행돼야 하고, stale_session 이 반환돼야 함
    cands = await scan_candidates(conn, claude_home, stale_days=90)
    categories = {c.category for c in cands}
    assert "stale_session" in categories
    assert "empty_project" not in categories
    assert "orphan_project" not in categories
    await conn.close()


# ---------- 11. size_bytes DESC 정렬 ----------


async def test_sort_by_size_desc(tmp_path: Path) -> None:
    """size_bytes 큰 후보가 먼저 나옴."""
    claude_home = tmp_path / "claude"
    # projects/ 없음 → empty/orphan 없음, stale 세션 2개로만 테스트

    overlay_db = tmp_path / "test.sqlite"
    conn = await open_db(overlay_db)
    await migrate(conn)

    now = datetime.now(UTC)
    stale_ts_a = (now - timedelta(days=100)).isoformat(timespec="seconds")
    stale_ts_b = (now - timedelta(days=110)).isoformat(timespec="seconds")

    for proj_id, cwd in [("-tmp-sort-a", "/tmp/sort-a"), ("-tmp-sort-b", "/tmp/sort-b")]:
        await conn.execute(
            """INSERT INTO projects(project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (proj_id, cwd, 0, stale_ts_a, stale_ts_a, 1, stale_ts_a),
        )

    # session-big: file_size=5000, session-small: file_size=100
    await conn.execute(
        """INSERT INTO sessions(session_id, project_id, jsonl_path, started_at, last_message_at,
                                message_count, user_message_count, assistant_message_count,
                                tool_use_count, subagent_count, file_size, file_mtime, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "session-big",
            "-tmp-sort-a",
            "/fake-a.jsonl",
            stale_ts_a,
            stale_ts_a,
            1,
            1,
            0,
            0,
            0,
            5000,
            stale_ts_a,
            stale_ts_a,
        ),
    )
    await conn.execute(
        """INSERT INTO sessions(session_id, project_id, jsonl_path, started_at, last_message_at,
                                message_count, user_message_count, assistant_message_count,
                                tool_use_count, subagent_count, file_size, file_mtime, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "session-small",
            "-tmp-sort-b",
            "/fake-b.jsonl",
            stale_ts_b,
            stale_ts_b,
            1,
            1,
            0,
            0,
            0,
            100,
            stale_ts_b,
            stale_ts_b,
        ),
    )
    await conn.commit()

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    sizes = [c.size_bytes for c in cands if c.size_bytes is not None]
    assert sizes == sorted(sizes, reverse=True), f"size_bytes DESC 정렬 실패: {sizes}"
    await conn.close()


# ---------- 12. summary dict 검증 (API 엔드포인트 smoke) ----------


async def test_summary_counts(hk_db: aiosqlite.Connection, hk_settings: Settings) -> None:
    """scan_candidates 결과로 summary dict 를 직접 집계 — 키·값 검증."""
    # DB에 empty_project 후보 시드
    await hk_db.execute(
        """INSERT OR IGNORE INTO projects
           (project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            "-tmp-empty-proj",
            "/tmp/empty-proj",
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
            datetime.now(UTC).isoformat(timespec="seconds"),
            0,
            datetime.now(UTC).isoformat(timespec="seconds"),
        ),
    )
    await hk_db.commit()

    cands = await scan_candidates(hk_db, hk_settings.paths.claude_home, stale_days=90)

    summary: dict[str, int] = {}
    for c in cands:
        summary[c.category] = summary.get(c.category, 0) + 1

    # 최소한 각 카테고리에 1개 이상 존재해야 함
    assert summary.get("stale_session", 0) >= 1
    assert summary.get("empty_project", 0) >= 1
    assert summary.get("orphan_project", 0) >= 1

    # summary 값은 모두 양의 정수
    for key, count in summary.items():
        assert count > 0, f"{key} count는 양수여야 함"
        assert key in {"stale_session", "empty_project", "orphan_project"}


# ---------- 보너스: _days_since timezone-aware 회귀 테스트 ----------


def test_days_since_z_suffix() -> None:
    """Z suffix ISO 8601 문자열을 fromisoformat 으로 파싱할 때 timezone-aware 처리 회귀."""
    ts = _ts(50)  # "2026-xx-xxTxx:xx:xx.000Z" 형태
    days = _days_since(ts)
    assert 48 <= days <= 52, f"Z suffix 파싱 실패 or 계산 오류: {days}일"


def test_days_since_invalid_returns_minus_one() -> None:
    """파싱 불가 입력에 대해 -1 반환 — ValueError 전파 금지."""
    assert _days_since("not-a-date") == -1
    assert _days_since("") == -1
    assert _days_since("2026/04/15") == -1


# ---------- 13. orphan_session 탐지 ----------


async def _seed_session(
    conn: aiosqlite.Connection,
    session_id: str,
    jsonl_path: str,
    days_ago: int = 10,
) -> None:
    """sessions + projects 에 최소한의 행을 직접 INSERT."""
    proj_id = f"-proj-{session_id}"
    ts = (datetime.now(UTC) - timedelta(days=days_ago)).isoformat(timespec="seconds")
    await conn.execute(
        """INSERT OR IGNORE INTO projects
           (project_id, decoded_cwd, cwd_exists, first_seen_at, last_active_at, session_count, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (proj_id, f"/fake/{session_id}", 0, ts, ts, 1, ts),
    )
    await conn.execute(
        """INSERT INTO sessions
           (session_id, project_id, jsonl_path, started_at, last_message_at,
            message_count, user_message_count, assistant_message_count,
            tool_use_count, subagent_count, file_size, file_mtime, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, proj_id, jsonl_path, ts, ts, 1, 1, 0, 0, 0, 100, ts, ts),
    )
    await conn.commit()


async def test_detect_orphan_session(tmp_path: Path) -> None:
    """jsonl_path 가 fs 에 없는 세션 → orphan_session 후보. category/reason 검증."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    conn = await open_db(tmp_path / "orphan.sqlite")
    await migrate(conn)
    await _seed_session(conn, "s-orphan", "/nonexistent/path/session.jsonl")

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan = [c for c in cands if c.category == "orphan_session"]
    ids = {c.entity_id for c in orphan}
    assert "s-orphan" in ids

    cand = next(c for c in orphan if c.entity_id == "s-orphan")
    assert "jsonl" in cand.reason.lower() or "사라짐" in cand.reason
    assert cand.metadata.get("jsonl_path") == "/nonexistent/path/session.jsonl"
    await conn.close()


async def test_orphan_session_pinned_excluded(tmp_path: Path) -> None:
    """orphan 후보지만 pin 있으면 orphan_session 에서 제외."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    conn = await open_db(tmp_path / "orphan-pin.sqlite")
    await migrate(conn)
    await _seed_session(conn, "s-orphan-pin", "/gone/session.jsonl")

    await conn.execute(
        "INSERT INTO pins(session_id, pinned_at) VALUES (?, ?)",
        ("s-orphan-pin", datetime.now(UTC).isoformat(timespec="seconds")),
    )
    await conn.commit()

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan_ids = {c.entity_id for c in cands if c.category == "orphan_session"}
    assert "s-orphan-pin" not in orphan_ids
    await conn.close()


async def test_orphan_session_tagged_excluded(tmp_path: Path) -> None:
    """orphan 후보지만 태그 있으면 orphan_session 에서 제외."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    conn = await open_db(tmp_path / "orphan-tag.sqlite")
    await migrate(conn)
    await _seed_session(conn, "s-orphan-tag", "/gone/session.jsonl")

    await conn.execute(
        "INSERT INTO tags(name, color, created_at) VALUES (?, ?, ?)",
        ("keep", None, datetime.now(UTC).isoformat(timespec="seconds")),
    )
    cur = await conn.execute("SELECT tag_id FROM tags WHERE name='keep'")
    tag_id = (await cur.fetchone())["tag_id"]
    await conn.execute(
        "INSERT INTO session_tags(session_id, tag_id, tagged_at) VALUES (?, ?, ?)",
        ("s-orphan-tag", tag_id, datetime.now(UTC).isoformat(timespec="seconds")),
    )
    await conn.commit()

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan_ids = {c.entity_id for c in cands if c.category == "orphan_session"}
    assert "s-orphan-tag" not in orphan_ids
    await conn.close()


async def test_orphan_takes_precedence_over_stale(tmp_path: Path) -> None:
    """90일+ 전 타임스탬프 + jsonl 없음 → orphan_session 으로만. stale_session 에는 안 나옴."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    conn = await open_db(tmp_path / "orphan-stale.sqlite")
    await migrate(conn)
    # 100일 전 + jsonl 없음 → stale 기준도 충족하지만 orphan 이 우선
    await _seed_session(conn, "s-both", "/gone/old-session.jsonl", days_ago=100)

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan_ids = {c.entity_id for c in cands if c.category == "orphan_session"}
    stale_ids = {c.entity_id for c in cands if c.category == "stale_session"}

    assert "s-both" in orphan_ids, "orphan_session 으로 잡혀야 함"
    assert "s-both" not in stale_ids, "exclude_ids 로 stale_session 에서 제외돼야 함"
    await conn.close()


async def test_real_jsonl_not_orphan(tmp_path: Path) -> None:
    """실제 jsonl 파일이 tmp_path 에 있으면 orphan_session 후보 아님."""
    claude_home = tmp_path / "claude"
    claude_home.mkdir(parents=True, exist_ok=True)

    real_jsonl = tmp_path / "real-session.jsonl"
    real_jsonl.write_text('{"type":"user"}\n')

    conn = await open_db(tmp_path / "orphan-real.sqlite")
    await migrate(conn)
    await _seed_session(conn, "s-real", str(real_jsonl))

    cands = await scan_candidates(conn, claude_home, stale_days=90)
    orphan_ids = {c.entity_id for c in cands if c.category == "orphan_session"}
    assert "s-real" not in orphan_ids
    await conn.close()
