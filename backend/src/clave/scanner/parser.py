"""JSONL line parser for ~/.claude/projects/<enc>/<sessionId>.jsonl files.

The on-disk schema has 4 record types: user, assistant, attachment, queue-operation.
We extract only the fields we need; unknown shapes are tolerated.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from clave.models import MessageItem


@dataclass(slots=True)
class ParseStats:
    total_lines: int = 0
    valid: int = 0
    invalid_json: int = 0
    unknown_type: int = 0


def _extract_text_from_content(content: object) -> str | None:
    """User content can be a string or a list of blocks; assistants are always blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts: list[str] = []
        thinkings: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "text" and isinstance(block.get("text"), str):
                texts.append(block["text"])
            elif t == "thinking" and isinstance(block.get("thinking"), str):
                thinkings.append(block["thinking"])
        if texts:
            return "\n".join(texts)
        if thinkings:
            return "\n".join(thinkings)
        return None
    return None


def _extract_tool_use(content: object) -> list[dict]:
    if not isinstance(content, list):
        return []
    out: list[dict] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            out.append(
                {
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": block.get("input"),
                }
            )
    return out


def extract_file_paths(tool_use_blocks: list[dict]) -> set[str]:
    """Extract file paths from tool_use input fields.

    Covers Read/Edit/Write (file_path) and Glob (path).
    Bash commands are skipped — too fuzzy to parse reliably.
    """
    paths: set[str] = set()
    for block in tool_use_blocks:
        inp = block.get("input")
        if not isinstance(inp, dict):
            continue
        if fp := inp.get("file_path"):
            if isinstance(fp, str):
                paths.add(fp)
        if p := inp.get("path"):
            if isinstance(p, str):
                paths.add(p)
    return paths


def normalise(line_obj: dict) -> MessageItem | None:
    """Convert a raw jsonl object into a MessageItem. Returns None if utterly unrecognisable."""
    rec_type = line_obj.get("type")
    if not isinstance(rec_type, str):
        return None

    msg = line_obj.get("message") if isinstance(line_obj.get("message"), dict) else None
    role = msg.get("role") if msg else None
    raw_content = msg.get("content") if msg else line_obj.get("content")
    text = _extract_text_from_content(raw_content)
    tool_use = _extract_tool_use(raw_content)

    return MessageItem(
        uuid=line_obj.get("uuid"),
        parent_uuid=line_obj.get("parentUuid"),
        timestamp=line_obj.get("timestamp"),
        type=rec_type,
        role=role,
        text=text,
        content=raw_content if isinstance(raw_content, list) else None,
        tool_use=tool_use or None,
        cwd=line_obj.get("cwd"),
        git_branch=line_obj.get("gitBranch"),
        cc_version=line_obj.get("version"),
    )


def iter_jsonl(path: Path, stats: ParseStats | None = None) -> Iterator[tuple[dict, MessageItem]]:
    """Stream-parse a jsonl file. Yields (raw_obj, normalised) for valid lines.

    Invalid JSON lines are counted in `stats` and skipped.
    """
    if stats is None:
        stats = ParseStats()
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stats.total_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                stats.invalid_json += 1
                continue
            if not isinstance(obj, dict):
                stats.invalid_json += 1
                continue
            item = normalise(obj)
            if item is None:
                stats.unknown_type += 1
                continue
            stats.valid += 1
            yield obj, item
