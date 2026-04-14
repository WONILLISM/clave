/**
 * TanStack Query mutation hooks.
 * Pin, Tag, Rescan 등 쓰기 작업.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type TagRow = components["schemas"]["TagRow"];
export type RescanResponse = components["schemas"]["RescanResponse"];

// ── Pin / Unpin ─────────────────────────────────────────────
export function usePinSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      api<void>(`/api/sessions/${sessionId}/pin`, { method: "POST" }),
    onSuccess: (_data, sessionId) => {
      qc.invalidateQueries({ queryKey: ["session", sessionId] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}

export function useUnpinSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      api<void>(`/api/sessions/${sessionId}/pin`, { method: "DELETE" }),
    onSuccess: (_data, sessionId) => {
      qc.invalidateQueries({ queryKey: ["session", sessionId] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}

// ── Tags ────────────────────────────────────────────────────
export function useAttachTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      name,
    }: {
      sessionId: string;
      name: string;
    }) =>
      api<TagRow>(`/api/sessions/${sessionId}/tags`, {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    onSuccess: (_data, { sessionId }) => {
      qc.invalidateQueries({ queryKey: ["session", sessionId] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}

export function useDetachTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      tagId,
    }: {
      sessionId: string;
      tagId: number;
    }) =>
      api<void>(`/api/sessions/${sessionId}/tags/${tagId}`, {
        method: "DELETE",
      }),
    onSuccess: (_data, { sessionId }) => {
      qc.invalidateQueries({ queryKey: ["session", sessionId] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}

// ── Rescan ──────────────────────────────────────────────────
export function useRescan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string | undefined = undefined) =>
      api<RescanResponse>("/api/admin/rescan", {
        method: "POST",
        body: JSON.stringify(
          projectId ? { project_id: projectId } : {},
        ),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.invalidateQueries({ queryKey: ["health"] });
    },
  });
}
