"""Knowledge Graph CRUD + Links + FTS + Promote E2E tests.

conftest 의 client fixture 는 이미 부트스트랩 스캔을 거쳐 session-aaa/bbb/ccc 가 존재.
"""

from __future__ import annotations

from httpx import AsyncClient

# ---------- CRUD ----------


async def test_create_and_get_knowledge(client: AsyncClient) -> None:
    r = await client.post(
        "/api/knowledge",
        json={"title": "First insight", "body": "Some body", "kind": "insight"},
    )
    assert r.status_code == 201
    body = r.json()
    kid = body["knowledge_id"]
    assert body["title"] == "First insight"
    assert body["kind"] == "insight"

    r = await client.get(f"/api/knowledge/{kid}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["item"]["title"] == "First insight"
    assert detail["links"] == []
    assert detail["backlinks"] == []


async def test_create_standalone(client: AsyncClient) -> None:
    """source_type/source_id 없이 독립 생성."""
    r = await client.post("/api/knowledge", json={"title": "Standalone"})
    assert r.status_code == 201
    body = r.json()
    assert body["source_type"] is None
    assert body["source_id"] is None


async def test_update_partial(client: AsyncClient) -> None:
    r = await client.post("/api/knowledge", json={"title": "Original"})
    kid = r.json()["knowledge_id"]

    r = await client.patch(f"/api/knowledge/{kid}", json={"title": "Updated"})
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"
    assert r.json()["body"] == ""  # unchanged


async def test_update_nonexistent(client: AsyncClient) -> None:
    r = await client.patch("/api/knowledge/99999", json={"title": "X"})
    assert r.status_code == 404


async def test_delete_knowledge(client: AsyncClient) -> None:
    r = await client.post("/api/knowledge", json={"title": "To delete"})
    kid = r.json()["knowledge_id"]

    r = await client.delete(f"/api/knowledge/{kid}")
    assert r.status_code == 204

    r = await client.get(f"/api/knowledge/{kid}")
    assert r.status_code == 404


async def test_delete_nonexistent(client: AsyncClient) -> None:
    r = await client.delete("/api/knowledge/99999")
    assert r.status_code == 404


# ---------- List / filter / pagination ----------


async def test_list_default(client: AsyncClient) -> None:
    await client.post("/api/knowledge", json={"title": "A", "kind": "insight"})
    await client.post("/api/knowledge", json={"title": "B", "kind": "recipe"})

    r = await client.get("/api/knowledge")
    assert r.status_code == 200
    body = r.json()
    assert body["total_count"] >= 2
    assert len(body["items"]) >= 2


async def test_list_filter_by_kind(client: AsyncClient) -> None:
    await client.post("/api/knowledge", json={"title": "K1", "kind": "snippet"})
    await client.post("/api/knowledge", json={"title": "K2", "kind": "question"})

    r = await client.get("/api/knowledge", params={"kind": "snippet"})
    body = r.json()
    for item in body["items"]:
        assert item["kind"] == "snippet"


async def test_list_pagination(client: AsyncClient) -> None:
    for i in range(5):
        await client.post("/api/knowledge", json={"title": f"Page {i}"})

    r = await client.get("/api/knowledge", params={"limit": 2, "offset": 0})
    body = r.json()
    assert len(body["items"]) == 2
    assert body["next_offset"] is not None

    r = await client.get("/api/knowledge", params={"limit": 2, "offset": body["next_offset"]})
    body2 = r.json()
    assert len(body2["items"]) == 2


# ---------- FTS ----------


async def test_fts_english(client: AsyncClient) -> None:
    await client.post("/api/knowledge", json={"title": "React hooks guide", "body": "useState"})

    r = await client.get("/api/knowledge", params={"q": "hooks"})
    body = r.json()
    assert any("hooks" in it["title"].lower() for it in body["items"])


async def test_fts_korean(client: AsyncClient) -> None:
    await client.post("/api/knowledge", json={"title": "테스트 작성법", "body": "pytest 활용"})

    r = await client.get("/api/knowledge", params={"q": "pytest"})
    body = r.json()
    assert any("pytest" in it["body"] for it in body["items"])


async def test_fts_no_results(client: AsyncClient) -> None:
    r = await client.get("/api/knowledge", params={"q": "xyznonexistent999"})
    assert r.json()["items"] == []


# ---------- Links ----------


async def test_create_link(client: AsyncClient) -> None:
    r1 = await client.post("/api/knowledge", json={"title": "Node A"})
    r2 = await client.post("/api/knowledge", json={"title": "Node B"})
    kid1, kid2 = r1.json()["knowledge_id"], r2.json()["knowledge_id"]

    r = await client.post(
        f"/api/knowledge/{kid1}/links",
        json={
            "from_type": "knowledge",
            "from_id": str(kid1),
            "to_type": "knowledge",
            "to_id": str(kid2),
            "relation": "related",
        },
    )
    assert r.status_code == 201
    assert r.json()["relation"] == "related"


async def test_duplicate_link_idempotent(client: AsyncClient) -> None:
    r1 = await client.post("/api/knowledge", json={"title": "Dup A"})
    r2 = await client.post("/api/knowledge", json={"title": "Dup B"})
    kid1, kid2 = r1.json()["knowledge_id"], r2.json()["knowledge_id"]

    link_json = {
        "from_type": "knowledge",
        "from_id": str(kid1),
        "to_type": "knowledge",
        "to_id": str(kid2),
    }
    r = await client.post(f"/api/knowledge/{kid1}/links", json=link_json)
    assert r.status_code == 201
    first_id = r.json()["link_id"]

    # Same link again — INSERT OR IGNORE, returns existing row.
    r = await client.post(f"/api/knowledge/{kid1}/links", json=link_json)
    assert r.status_code == 201
    assert r.json()["link_id"] == first_id


async def test_delete_link(client: AsyncClient) -> None:
    r1 = await client.post("/api/knowledge", json={"title": "Del Link A"})
    r2 = await client.post("/api/knowledge", json={"title": "Del Link B"})
    kid1, kid2 = r1.json()["knowledge_id"], r2.json()["knowledge_id"]

    r = await client.post(
        f"/api/knowledge/{kid1}/links",
        json={
            "from_type": "knowledge",
            "from_id": str(kid1),
            "to_type": "knowledge",
            "to_id": str(kid2),
        },
    )
    link_id = r.json()["link_id"]

    r = await client.delete(f"/api/knowledge/links/{link_id}")
    assert r.status_code == 204

    r = await client.delete(f"/api/knowledge/links/{link_id}")
    assert r.status_code == 404


async def test_bidirectional_query(client: AsyncClient) -> None:
    """links/backlinks 가 양방향으로 조회되는지 확인."""
    r1 = await client.post("/api/knowledge", json={"title": "Bi A"})
    r2 = await client.post("/api/knowledge", json={"title": "Bi B"})
    kid1, kid2 = r1.json()["knowledge_id"], r2.json()["knowledge_id"]

    await client.post(
        f"/api/knowledge/{kid1}/links",
        json={
            "from_type": "knowledge",
            "from_id": str(kid1),
            "to_type": "knowledge",
            "to_id": str(kid2),
            "relation": "derives_from",
        },
    )

    # kid1 의 detail → links 에 보임
    r = await client.get(f"/api/knowledge/{kid1}")
    assert len(r.json()["links"]) >= 1

    # kid2 의 detail → backlinks 에 보임
    r = await client.get(f"/api/knowledge/{kid2}")
    assert len(r.json()["backlinks"]) >= 1


async def test_delete_knowledge_cascades_links(client: AsyncClient) -> None:
    """Knowledge 삭제 시 관련 links 도 정리."""
    r1 = await client.post("/api/knowledge", json={"title": "Cascade A"})
    r2 = await client.post("/api/knowledge", json={"title": "Cascade B"})
    kid1, kid2 = r1.json()["knowledge_id"], r2.json()["knowledge_id"]

    r = await client.post(
        f"/api/knowledge/{kid1}/links",
        json={
            "from_type": "knowledge",
            "from_id": str(kid1),
            "to_type": "knowledge",
            "to_id": str(kid2),
        },
    )
    link_id = r.json()["link_id"]

    # kid1 삭제 → 링크도 사라져야
    await client.delete(f"/api/knowledge/{kid1}")

    r = await client.get(f"/api/knowledge/{kid2}")
    assert r.json()["backlinks"] == []

    r = await client.delete(f"/api/knowledge/links/{link_id}")
    assert r.status_code == 404


# ---------- Promote ----------


async def test_promote_highlight(client: AsyncClient) -> None:
    """Highlight → Knowledge 승격 + auto session link."""
    # highlight 생성
    r = await client.post(
        "/api/sessions/session-aaa/highlights",
        json={"text": "Important finding", "kind": "insight"},
    )
    hid = r.json()["highlight_id"]

    r = await client.post(
        "/api/knowledge/from-highlight",
        json={"highlight_id": hid, "kind": "insight"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Important finding"  # auto-title from text
    assert body["source_type"] == "highlight"
    assert body["source_id"] == str(hid)

    # Detail 에 derives_from session link 가 존재해야.
    r = await client.get(f"/api/knowledge/{body['knowledge_id']}")
    detail = r.json()
    assert any(
        lnk["to_type"] == "session" and lnk["relation"] == "derives_from" for lnk in detail["links"]
    )


async def test_promote_with_custom_title(client: AsyncClient) -> None:
    r = await client.post(
        "/api/sessions/session-bbb/highlights",
        json={"text": "Some text here"},
    )
    hid = r.json()["highlight_id"]

    r = await client.post(
        "/api/knowledge/from-highlight",
        json={"highlight_id": hid, "title": "Custom Title"},
    )
    assert r.status_code == 201
    assert r.json()["title"] == "Custom Title"


async def test_promote_nonexistent_highlight(client: AsyncClient) -> None:
    r = await client.post(
        "/api/knowledge/from-highlight",
        json={"highlight_id": 99999},
    )
    assert r.status_code == 404
