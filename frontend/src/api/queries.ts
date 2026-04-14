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
