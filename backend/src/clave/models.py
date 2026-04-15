"""Pydantic domain & DTO models."""

from __future__ import annotations

from typing import Any, Literal

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


class HighlightRow(BaseModel):
    """세션 메시지에서 사용자가 선택·저장한 텍스트 인용."""

    highlight_id: int
    session_id: str
    message_uuid: str | None = None
    text: str
    kind: str  # 'insight' 기본, 추후 'prompt'|'recipe'|'snippet' 확장 여지
    created_at: str


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


class CreateHighlightRequest(BaseModel):
    message_uuid: str | None = None
    text: str
    kind: str = "insight"


class SearchResponse(BaseModel):
    items: list[SessionListItem]
    query: str


class ArtifactPathItem(BaseModel):
    """/artifacts 카탈로그의 한 행 — 1 path = 1 항목."""

    path: str
    last_modified: str  # MAX(created_at)
    edit_count: int  # 이 path 에 대한 전체 Write/Edit/MultiEdit 이벤트 수
    session_count: int  # 이 path 를 건드린 고유 세션 수
    tools: list[str]  # 고유 tool_name (예: ["Edit", "Write"])
    last_session_id: str
    last_session_summary: str | None = None
    exists: bool  # 동적 계산 (응답 직전 os.path.exists)


class ArtifactPathListResponse(BaseModel):
    items: list[ArtifactPathItem]
    next_offset: int | None = None


class ArtifactSessionRef(BaseModel):
    """특정 path 를 건드린 한 세션 요약 (path 역참조 drawer)."""

    session_id: str
    session_summary: str | None = None
    decoded_cwd: str | None = None
    tool_name: str  # 이 세션에서 마지막으로 쓴 tool
    message_uuid: str | None = None  # 이 세션에서 마지막 tool_use 의 uuid
    created_at: str  # 이 세션에서의 가장 최근 수정 시각 (MAX)
    edit_count: int  # 이 세션 내 해당 path 수정 횟수


# ---------- Housekeeping ----------

HousekeepingCategory = Literal["stale_session", "empty_project", "orphan_project", "orphan_session"]


class HousekeepingCandidateItem(BaseModel):
    category: HousekeepingCategory  # OpenAPI enum 으로 생성 → 프론트 타입 분기 안전
    entity_id: str
    display_name: str
    reason: str
    size_bytes: int | None = None
    last_activity: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HousekeepingScanResponse(BaseModel):
    items: list[HousekeepingCandidateItem]
    scanned_at: str
    summary: dict[
        HousekeepingCategory, int
    ]  # {"stale_session": 5, "empty_project": 1, "orphan_project": 2, "orphan_session": 3}
    total_size_bytes: int  # 전체 후보 크기 합 (UI 배너용)


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
