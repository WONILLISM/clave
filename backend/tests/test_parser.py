from __future__ import annotations

import json
from pathlib import Path

from clave.scanner.parser import ParseStats, iter_jsonl, normalise


def test_normalise_user_string_content() -> None:
    obj = {
        "type": "user",
        "uuid": "u1",
        "timestamp": "2026-04-13T00:00:00Z",
        "message": {"role": "user", "content": "hello"},
        "cwd": "/tmp",
    }
    item = normalise(obj)
    assert item is not None
    assert item.type == "user"
    assert item.role == "user"
    assert item.text == "hello"
    assert item.cwd == "/tmp"


def test_normalise_assistant_blocks_with_tool_use() -> None:
    obj = {
        "type": "assistant",
        "uuid": "a1",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "hmm"},
                {"type": "text", "text": "answer"},
                {"type": "tool_use", "id": "t1", "name": "Read", "input": {"x": 1}},
            ],
        },
    }
    item = normalise(obj)
    assert item is not None
    assert item.text == "answer"  # text wins over thinking
    assert item.tool_use is not None
    assert len(item.tool_use) == 1
    assert item.tool_use[0]["name"] == "Read"


def test_iter_jsonl_skips_invalid_and_empty(tmp_path: Path) -> None:
    p = tmp_path / "x.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"type": "user", "message": {"role": "user", "content": "a"}}),
                "{not json}",
                "",
                json.dumps({"type": "queue-operation"}),
            ]
        )
    )
    stats = ParseStats()
    items = [it for _raw, it in iter_jsonl(p, stats)]
    assert len(items) == 2
    assert stats.invalid_json == 1
    assert stats.valid == 2
