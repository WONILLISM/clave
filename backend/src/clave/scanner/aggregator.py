"""Roll up a stream of parsed messages into a SessionSummary used to upsert sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from clave.scanner.parser import ParseStats, extract_file_paths, iter_jsonl


@dataclass(slots=True)
class SessionSummary:
    session_id: str
    started_at: str = ""
    last_message_at: str = ""
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    tool_use_count: int = 0
    summary: str | None = None
    git_branch: str | None = None
    cc_version: str | None = None
    cwd_from_user_msg: str | None = None
    file_paths: set[str] = field(default_factory=set)
    parse_stats: ParseStats = field(default_factory=ParseStats)


def aggregate_jsonl(path: Path, session_id: str) -> SessionSummary:
    """Single-pass aggregation. session_id must match the file (caller's responsibility)."""
    s = SessionSummary(session_id=session_id)
    for _raw, item in iter_jsonl(path, s.parse_stats):
        ts = item.timestamp
        if ts:
            if not s.started_at or ts < s.started_at:
                s.started_at = ts
            if ts > s.last_message_at:
                s.last_message_at = ts

        s.message_count += 1
        if item.type == "user":
            s.user_message_count += 1
            if s.summary is None and item.text:
                s.summary = item.text[:200]
            if s.cwd_from_user_msg is None and item.cwd:
                s.cwd_from_user_msg = item.cwd
        elif item.type == "assistant":
            s.assistant_message_count += 1
            if item.tool_use:
                s.tool_use_count += len(item.tool_use)
                s.file_paths.update(extract_file_paths(item.tool_use))

        if item.git_branch:
            s.git_branch = item.git_branch
        if item.cc_version:
            s.cc_version = item.cc_version

    return s
