from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["indexed_sessions"] == 3


async def test_projects(client: AsyncClient) -> None:
    r = await client.get("/api/projects")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2


async def test_sessions_filtered(client: AsyncClient) -> None:
    r = await client.get("/api/sessions", params={"project_id": "-tmp-proj-a"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    sids = {x["session_id"] for x in body["items"]}
    assert sids == {"session-aaa", "session-bbb"}


async def test_session_detail(client: AsyncClient) -> None:
    r = await client.get("/api/sessions/session-aaa")
    assert r.status_code == 200
    body = r.json()
    assert body["session"]["session_id"] == "session-aaa"
    assert len(body["messages"]) >= 2  # user + assistant + queue-op (3)


async def test_pin_and_filter(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/session-aaa/pin")
    assert r.status_code == 204
    r = await client.get("/api/sessions", params={"pinned": "true"})
    body = r.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["session_id"] == "session-aaa"
    assert body["items"][0]["pinned"] is True
    r = await client.delete("/api/sessions/session-aaa/pin")
    assert r.status_code == 204


async def test_tag_attach_and_filter(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/session-bbb/tags", json={"name": "important"})
    assert r.status_code == 201
    r = await client.get("/api/sessions", params={"tag": "important"})
    body = r.json()
    assert len(body["items"]) == 1
    assert "important" in body["items"][0]["tags"]


async def test_notes_lifecycle(client: AsyncClient) -> None:
    r = await client.post("/api/sessions/session-ccc/notes", json={"body": "remember this"})
    assert r.status_code == 201
    note_id = r.json()["note_id"]

    r = await client.get("/api/sessions/session-ccc/notes")
    assert len(r.json()) == 1

    r = await client.patch(f"/api/notes/{note_id}", json={"body": "updated"})
    assert r.json()["body"] == "updated"

    r = await client.delete(f"/api/notes/{note_id}")
    assert r.status_code == 204


async def test_rescan(client: AsyncClient) -> None:
    r = await client.post("/api/admin/rescan", json={})
    assert r.status_code == 200
    body = r.json()
    # Bootstrap already happened in lifespan, so this should be all skips.
    assert body["scanned_sessions"] == 0
    assert body["skipped_sessions"] == 3
