"""Pydantic domain & DTO models."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------- Domain rows (DB-shaped) ----------


class ProjectRow(BaseModel):
    project_id: str
    decoded_cwd: str
    cwd_exists: bool
    first_seen_at: str
    last_active_at: str
    session_count: int
    indexed_at: str


class SessionRow(BaseModel):
    session_id: str
    project_id: str
    jsonl_path: str
    started_at: str
    last_message_at: str
    message_count: int
    user_message_count: int
    assistant_message_count: int
    tool_use_count: int
    subagent_count: int
    summary: str | None = None
    git_branch: str | None = None
    cc_version: str | None = None
    file_paths: str = ""
    file_size: int
    file_mtime: str
    indexed_at: str


class TagRow(BaseModel):
    tag_id: int
    name: str
    color: str | None = None
    created_at: str


class NoteRow(BaseModel):
    note_id: int
    session_id: str
    body: str
    created_at: str
    updated_at: str


class ArtifactRow(BaseModel):
    """세션이 Write/Edit/MultiEdit 로 만든 파일 한 항목."""

    artifact_id: int
    session_id: str
    path: str
    tool_name: str  # 'Write' | 'Edit' | 'MultiEdit'
    message_uuid: str | None = None
    created_at: str
    exists: bool  # 동적 계산 (응답 직전 os.path.exists)


# ---------- API response wrappers ----------


class HealthResponse(BaseModel):
    status: str
    db_path: str
    indexed_sessions: int


class ProjectListItem(BaseModel):
    project_id: str
    decoded_cwd: str
    cwd_exists: bool
    session_count: int
    last_active_at: str


class SessionListItem(BaseModel):
    session_id: str
    project_id: str
    decoded_cwd: str
    started_at: str
    last_message_at: str
    message_count: int
    user_message_count: int
    assistant_message_count: int
    tool_use_count: int
    subagent_count: int
    summary: str | None
    git_branch: str | None
    cc_version: str | None
    pinned: bool
    tags: list[str]


class SessionListResponse(BaseModel):
    items: list[SessionListItem]
    next_cursor: str | None = None


class TagListItem(BaseModel):
    tag_id: int
    name: str
    color: str | None
    session_count: int


class CreateTagRequest(BaseModel):
    name: str
    color: str | None = None


class AttachTagRequest(BaseModel):
    tag_id: int | None = None
    name: str | None = None


class CreateNoteRequest(BaseModel):
    body: str


class UpdateNoteRequest(BaseModel):
    body: str


class SearchResponse(BaseModel):
    items: list[SessionListItem]
    query: str


class ArtifactListItem(ArtifactRow):
    """Global 카탈로그용. ArtifactRow 와 동일 필드 + 세션 요약 메타."""

    session_summary: str | None = None
    session_decoded_cwd: str | None = None


class ArtifactListResponse(BaseModel):
    items: list[ArtifactListItem]
    next_cursor: str | None = None


class RescanRequest(BaseModel):
    project_id: str | None = None


class RescanResponse(BaseModel):
    scanned_projects: int
    scanned_sessions: int
    skipped_sessions: int
    elapsed_ms: float


# ---------- Session detail (messages streamed from jsonl) ----------


class MessageItem(BaseModel):
    """A single jsonl line, normalised into a UI-friendly shape."""

    uuid: str | None = None
    parent_uuid: str | None = None
    timestamp: str | None = None
    type: str  # "user" | "assistant" | "attachment" | "queue-operation" | "unknown"
    role: str | None = None  # for user/assistant
    text: str | None = None  # plain text content if any
    content: list[dict] | None = None  # raw content blocks for assistant
    tool_use: list[dict] | None = None  # extracted tool_use blocks
    cwd: str | None = None
    git_branch: str | None = None
    cc_version: str | None = None
    raw: dict | None = None  # original line for debugging (omitted by default)


class SessionDetailResponse(BaseModel):
    session: SessionListItem
    messages: list[MessageItem]
    has_more: bool
    next_offset: int = Field(0, description="line offset to pass next time")
