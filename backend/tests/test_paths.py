from __future__ import annotations

from pathlib import Path

from clave.paths import cwd_exists, decode_project_id


def test_decode_when_path_exists(tmp_path: Path) -> None:
    # Use a hyphen-free subdirectory so encoding is bijective.
    target = tmp_path / "alpha" / "beta"
    target.mkdir(parents=True)
    encoded = str(target).replace("/", "-")
    decoded = decode_project_id(encoded)
    assert decoded == str(target)
    assert cwd_exists(decoded)


def test_decode_when_path_does_not_exist() -> None:
    decoded = decode_project_id("-tmp-this-does-not-exist-anywhere-xyz")
    # Naive decode is the fallback
    assert decoded.startswith("/")
    assert not cwd_exists(decoded)


def test_decode_passthrough_for_unencoded() -> None:
    assert decode_project_id("plain-name") == "plain-name"
