"""Runtime configuration loaded from ~/.clave/config.toml + env."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathsConfig(BaseModel):
    claude_home: Path = Field(default_factory=lambda: Path("~/.claude").expanduser())
    overlay_db: Path = Field(default_factory=lambda: Path("~/.clave/overlay.sqlite").expanduser())
    trash_dir: Path = Field(default_factory=lambda: Path("~/.clave/trash").expanduser())


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765


class ScannerConfig(BaseModel):
    include_subagents: bool = False  # W1: locked off


class Settings(BaseSettings):
    paths: PathsConfig = PathsConfig()
    server: ServerConfig = ServerConfig()
    scanner: ScannerConfig = ScannerConfig()

    model_config = SettingsConfigDict(env_prefix="CLAVE_", env_nested_delimiter="__")


def _expand(value: object) -> object:
    if isinstance(value, str) and value.startswith("~"):
        return str(Path(value).expanduser())
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings, layering: defaults < TOML file < env vars.

    TOML location: $CLAVE_CONFIG, else ~/.clave/config.toml. Missing file => defaults.
    """
    if config_path is None:
        env = os.environ.get("CLAVE_CONFIG")
        config_path = Path(env).expanduser() if env else Path("~/.clave/config.toml").expanduser()

    file_data: dict = {}
    if config_path.is_file():
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
        file_data = _expand(raw)  # type: ignore[assignment]

    return Settings(**file_data)
