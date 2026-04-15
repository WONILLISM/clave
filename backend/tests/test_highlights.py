"""Highlight CRUD E2E tests.

conftest 의 client fixture 는 이미 부트스트랩 스캔을 거쳐 session-aaa/bbb/ccc 가 존재.
"""

from __future__ import annotations

import aiosqlite
from httpx import AsyncClient


async def test_create_and_list_highlight(client: AsyncClient) -> None:
    r = await client.post(
        "/api/sessions/session-aaa/highlights",
        json={"message_uuid": "a1", "text": "Hi", "kind": "insight"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["text"] == "Hi"
    assert body["kind"] == "insight"
    assert body["message_uuid"] == "a1"

    r = await client.get("/api/sessions/session-aaa/highlights")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["text"] == "Hi"


async def test_delete_highlight(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/session-bbb/highlights", json={"text": "keep me"})
    hid = r.json()["highlight_id"]

    r = await client.delete(f"/api/highlights/{hid}")
    assert r.status_code == 204

    r = await client.get("/api/sessions/session-bbb/highlights")
    assert r.json() == []

    # 두 번째 삭제는 404
    r = await client.delete(f"/api/highlights/{hid}")
    assert r.status_code == 404


async def test_create_requires_valid_session(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/no-such-session/highlights", json={"text": "x"})
    assert r.status_code == 404


async def test_create_rejects_empty_text(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/session-ccc/highlights", json={"text": "   "})
    assert r.status_code == 400


async def test_cascade_on_session_delete(db_scanned: aiosqlite.Connection) -> None:
    """세션 행 삭제 시 FK CASCADE 로 하이라이트도 사라져야 함."""
    await db_scanned.execute(
        "INSERT INTO highlights (session_id, message_uuid, text, kind, created_at) "
        "VALUES ('session-aaa', 'a1', 'bye', 'insight', '2026-04-15T00:00:00Z')"
    )
    await db_scanned.commit()

    cur = await db_scanned.execute(
        "SELECT COUNT(*) FROM highlights WHERE session_id = 'session-aaa'"
    )
    (before,) = await cur.fetchone()  # type: ignore[misc]
    assert before == 1

    await db_scanned.execute("DELETE FROM sessions WHERE session_id = 'session-aaa'")
    await db_scanned.commit()

    cur = await db_scanned.execute(
        "SELECT COUNT(*) FROM highlights WHERE session_id = 'session-aaa'"
    )
    (after,) = await cur.fetchone()  # type: ignore[misc]
    assert after == 0
