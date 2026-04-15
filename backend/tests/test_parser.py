from __future__ import annotations

import json
from pathlib import Path

from clave.scanner.parser import (
    ParseStats,
    extract_artifacts,
    extract_file_paths,
    iter_jsonl,
    normalise,
)


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


def test_extract_artifacts_only_write_edit_multiedit() -> None:
    blocks = [
        {"name": "Write", "input": {"file_path": "/a.md", "content": "..."}},
        {"name": "Edit", "input": {"file_path": "/b.ts", "old_string": "x", "new_string": "y"}},
        {"name": "MultiEdit", "input": {"file_path": "/c.py", "edits": []}},
        {"name": "Read", "input": {"file_path": "/d.md"}},  # 제외 (참조)
        {"name": "Glob", "input": {"path": "**/*.md"}},  # 제외
        {"name": "Bash", "input": {"command": "echo hi"}},  # 제외
        {"name": "Write", "input": {"file_path": ""}},  # 빈 경로 제외
        {"name": "Write", "input": {}},  # file_path 없음 제외
    ]
    result = extract_artifacts(blocks)
    assert result == [
        ("/a.md", "Write"),
        ("/b.ts", "Edit"),
        ("/c.py", "MultiEdit"),
    ]


def test_extract_file_paths_still_includes_reads() -> None:
    """Artifact 분리 이후에도 file_paths(검색용)는 Read 포함 유지."""
    blocks = [
        {"name": "Read", "input": {"file_path": "/r.md"}},
        {"name": "Write", "input": {"file_path": "/w.md"}},
    ]
    paths = extract_file_paths(blocks)
    assert paths == {"/r.md", "/w.md"}


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
