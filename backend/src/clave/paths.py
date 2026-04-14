"""Helpers for the ~/.claude/projects/<encoded>/ path encoding scheme.

Encoding rule (observed):
    /Users/foo/bar  ->  -Users-foo-bar
i.e. each "/" is replaced with "-", with a leading "-" prefix.

This is lossy: original paths containing "-" become ambiguous after decoding.
We provide best-effort decoding; the *authoritative* cwd should always be
read from a session's first user message (`cwd` field) when available.
"""

from __future__ import annotations

from pathlib import Path


def decode_project_id(project_id: str) -> str:
    """Best-effort decode of an encoded project directory name into an absolute path.

    The encoding is lossy because original paths can already contain "-".
    Strategy: walk down the filesystem one segment at a time, picking the longest
    consecutive group of "-"-joined parts that resolves to a real directory.
    Falls back to a naive replace-all if no real directory matches.
    """
    if not project_id.startswith("-"):
        return project_id

    parts = project_id[1:].split("-")
    naive = "/" + "/".join(parts)
    if Path(naive).is_dir():
        return naive

    current = Path("/")
    i = 0
    while i < len(parts):
        # Find longest j (>= i) such that current/(parts[i]..parts[j] joined by "-") exists.
        best_j: int | None = None
        best_path: Path | None = None
        for j in range(i, len(parts)):
            candidate = current / "-".join(parts[i : j + 1])
            if candidate.is_dir():
                best_j = j
                best_path = candidate
        if best_path is None or best_j is None:
            # No further match; append remaining as one segment using naive "/".
            tail_segments = parts[i:]
            current = current / "/".join(tail_segments)
            break
        current = best_path
        i = best_j + 1

    decoded = str(current)
    return decoded if decoded != "/" else naive


def cwd_exists(decoded_cwd: str) -> bool:
    return Path(decoded_cwd).is_dir()
