"""Architectural-constraint tests.

These enforce the harness rules from CLAUDE.md:
  - No ORM (SQLAlchemy/Tortoise/Peewee) imports anywhere.
  - Module dependency direction:
        api      → scanner, overlay, models, config, paths
        scanner  → overlay, models, config, paths
        overlay  → models, config
    i.e. no upward imports (overlay must not import scanner/api; scanner must not import api).
  - No code accidentally writes inside ~/.claude/.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "clave"

FORBIDDEN_PACKAGES = {
    "sqlalchemy",
    "tortoise",
    "peewee",
    "alembic",
    "django",
}


def _python_files() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def _imports_in(path: Path) -> set[str]:
    """Return the set of top-level module names imported by `path`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                out.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Keep the full dotted path so we can reason about clave.* layering.
                out.add(node.module)
                out.add(node.module.split(".")[0])
    return out


def test_no_orm_imports() -> None:
    offenders: list[tuple[Path, str]] = []
    for p in _python_files():
        for mod in _imports_in(p):
            if mod.split(".")[0] in FORBIDDEN_PACKAGES:
                offenders.append((p, mod))
    assert not offenders, f"ORM/forbidden imports found: {offenders}"


def _layer_of(module: str) -> str | None:
    """Map a 'clave.foo.bar' import to its layer name, or None if not relevant."""
    if not module.startswith("clave."):
        return None
    parts = module.split(".")
    if len(parts) < 2:
        return None
    second = parts[1]
    if second in {"api", "scanner", "overlay"}:
        return second
    return None  # models, config, paths, logging_setup are leaf — anyone can use them


# Allowed: lower layers cannot import upper layers.
# Layer order (high → low): api > scanner > overlay
_FORBIDDEN_EDGES = {
    "overlay": {"scanner", "api"},
    "scanner": {"api"},
    "api": set(),  # api may import everything
}


def test_layering() -> None:
    offenders: list[tuple[Path, str, str]] = []
    for p in _python_files():
        rel = p.relative_to(SRC)
        if not rel.parts:
            continue
        my_layer = rel.parts[0] if rel.parts[0] in {"api", "scanner", "overlay"} else None
        if my_layer is None:
            continue
        forbidden = _FORBIDDEN_EDGES[my_layer]
        for mod in _imports_in(p):
            target = _layer_of(mod)
            if target and target in forbidden:
                offenders.append((p, my_layer, mod))
    assert not offenders, f"Layering violations: {offenders}"


_WRITE_CALL_NAMES = {
    "write_text",
    "write_bytes",
    "mkdir",
    "touch",
    "unlink",
    "rmdir",
    "rename",
    "replace",
    "remove",
    "removedirs",
    "makedirs",
}


def _calls_write_against_claude_home(path: Path) -> list[str]:
    """Return offending source-line snippets where a write op targets a `.claude` path."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        # open("...", "w") with literal path
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            mode = ""
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(c in mode for c in ("w", "a", "x")) and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and ".claude" in str(first.value):
                    offenders.append(f"open(...) write @ line {node.lineno}")
        # Method calls like p.write_text(...), p.mkdir(...), Path("~/.claude").mkdir()
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _WRITE_CALL_NAMES:
                src = ast.unparse(node)
                if ".claude" in src:
                    offenders.append(f"{node.func.attr}(...) @ line {node.lineno}")
    return offenders


def test_no_writes_under_claude_home() -> None:
    """Production code must not call write APIs against ~/.claude/ paths."""
    bad: list[tuple[Path, list[str]]] = []
    for p in _python_files():
        offenders = _calls_write_against_claude_home(p)
        if offenders:
            bad.append((p, offenders))
    assert not bad, f"Write operations targeting ~/.claude/ found: {bad}"
