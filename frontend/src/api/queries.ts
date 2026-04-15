/**
 * TanStack Query thin hooks.
 * schema.ts (openapi-typescript 자동생성) 에서 타입을 끌어다 씀.
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { components, operations } from "./schema";

// ── 응답 타입 별칭 ─────────────────────────────────────────
export type HealthResponse = components["schemas"]["HealthResponse"];
export type ProjectListItem = components["schemas"]["ProjectListItem"];
export type SessionListItem = components["schemas"]["SessionListItem"];
export type SessionListResponse = components["schemas"]["SessionListResponse"];
export type SessionDetailResponse = components["schemas"]["SessionDetailResponse"];
export type MessageItem = components["schemas"]["MessageItem"];

// sessions 쿼리 파라미터
export type SessionsQuery =
  operations["list_sessions_endpoint_api_sessions_get"]["parameters"]["query"];

export type TagListItem = components["schemas"]["TagListItem"];
export type NoteRow = components["schemas"]["NoteRow"];
export type ArtifactPathItem = components["schemas"]["ArtifactPathItem"];
export type ArtifactPathListResponse =
  components["schemas"]["ArtifactPathListResponse"];
export type ArtifactSessionRef = components["schemas"]["ArtifactSessionRef"];

export type HighlightRow = components["schemas"]["HighlightRow"];

// 검색 응답 (schema.ts 재생성 전이므로 인라인 정의)
export interface SearchResponse {
  items: SessionListItem[];
  query: string;
}

// ── Tags ────────────────────────────────────────────────────
export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: () => api<TagListItem[]>("/api/tags"),
  });
}

// ── Health ──────────────────────────────────────────────────
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api<HealthResponse>("/api/health"),
    refetchInterval: 5_000,
  });
}

// ── Projects ────────────────────────────────────────────────
export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => api<ProjectListItem[]>("/api/projects"),
  });
}

// ── Sessions (list) ─────────────────────────────────────────
export function useSessions(params?: SessionsQuery) {
  const search = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v != null) search.set(k, String(v));
    }
  }
  const qs = search.toString();
  return useQuery({
    queryKey: ["sessions", params ?? {}],
    queryFn: () =>
      api<SessionListResponse>(`/api/sessions${qs ? `?${qs}` : ""}`),
  });
}

// ── Session detail ──────────────────────────────────────────
export function useSession(id: string, offset = 0, limit = 200) {
  return useQuery({
    queryKey: ["session", id, offset],
    queryFn: () =>
      api<SessionDetailResponse>(
        `/api/sessions/${id}?offset=${offset}&limit=${limit}`,
      ),
    enabled: !!id,
  });
}

// ── Notes ───────────────────────────────────────────────────
export function useNotes(sessionId: string) {
  return useQuery({
    queryKey: ["notes", sessionId],
    queryFn: () => api<NoteRow[]>(`/api/sessions/${sessionId}/notes`),
    enabled: !!sessionId,
  });
}

// ── Highlights ──────────────────────────────────────────────
export function useHighlights(sessionId: string) {
  return useQuery({
    queryKey: ["highlights", sessionId],
    queryFn: () =>
      api<HighlightRow[]>(`/api/sessions/${sessionId}/highlights`),
    enabled: !!sessionId,
  });
}

// ── Artifacts (path-grouped 카탈로그 + 세션 역참조) ────────
export function useArtifactPaths(params?: {
  limit?: number;
  offset?: number;
  q?: string;
}) {
  const qs = new URLSearchParams();
  if (params?.limit != null) qs.set("limit", String(params.limit));
  if (params?.offset != null) qs.set("offset", String(params.offset));
  if (params?.q) qs.set("q", params.q);
  const s = qs.toString();
  return useQuery({
    queryKey: ["artifact-paths", params ?? {}],
    queryFn: () =>
      api<ArtifactPathListResponse>(`/api/artifacts/paths${s ? `?${s}` : ""}`),
  });
}

export function useArtifactSessions(path: string | null) {
  return useQuery({
    queryKey: ["artifact-sessions", path],
    queryFn: () =>
      api<ArtifactSessionRef[]>(
        `/api/artifacts/sessions?path=${encodeURIComponent(path!)}`,
      ),
    enabled: !!path,
  });
}

// ── Search ──────────────────────────────────────────────────
export function useSearch(q: string) {
  return useQuery({
    queryKey: ["search", q],
    queryFn: () =>
      api<SearchResponse>(`/api/search?q=${encodeURIComponent(q)}`),
    enabled: q.length >= 2,
    placeholderData: (prev) => prev,
  });
}
