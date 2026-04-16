/**
 * TanStack Query mutation hooks.
 * Pin, Tag, Rescan 등 쓰기 작업.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type { components } from "./schema";

export type TagRow = components["schemas"]["TagRow"];
export type NoteRow = components["schemas"]["NoteRow"];
export type HighlightRow = components["schemas"]["HighlightRow"];
export type CreateHighlightRequest =
  components["schemas"]["CreateHighlightRequest"];
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

// ── Notes ───────────────────────────────────────────────────
export function useCreateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      body,
    }: {
      sessionId: string;
      body: string;
    }) =>
      api<NoteRow>(`/api/sessions/${sessionId}/notes`, {
        method: "POST",
        body: JSON.stringify({ body }),
      }),
    onSuccess: (_data, { sessionId }) => {
      qc.invalidateQueries({ queryKey: ["notes", sessionId] });
    },
  });
}

export function useUpdateNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { noteId: number; sessionId: string; body: string }) =>
      api<NoteRow>(`/api/notes/${vars.noteId}`, {
        method: "PATCH",
        body: JSON.stringify({ body: vars.body }),
      }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["notes", vars.sessionId] });
    },
  });
}

export function useDeleteNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { noteId: number; sessionId: string }) =>
      api<void>(`/api/notes/${vars.noteId}`, { method: "DELETE" }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["notes", vars.sessionId] });
    },
  });
}

// ── Highlights ──────────────────────────────────────────────
export function useCreateHighlight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      body,
    }: {
      sessionId: string;
      body: CreateHighlightRequest;
    }) =>
      api<HighlightRow>(`/api/sessions/${sessionId}/highlights`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (_data, { sessionId }) => {
      qc.invalidateQueries({ queryKey: ["highlights", sessionId] });
    },
  });
}

export function useDeleteHighlight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { highlightId: number; sessionId: string }) =>
      api<void>(`/api/highlights/${vars.highlightId}`, { method: "DELETE" }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["highlights", vars.sessionId] });
    },
  });
}

// ── Session delete ──────────────────────────────────────────
export function useDeleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) =>
      api<void>(`/api/sessions/${sessionId}`, { method: "DELETE" }),
    onSuccess: (_data, sessionId) => {
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.invalidateQueries({ queryKey: ["session", sessionId] });
    },
  });
}

// ── Knowledge ──────────────────────────────────────────────
export function useCreateKnowledge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      title: string;
      body?: string;
      kind?: string;
      source_type?: string;
      source_id?: string;
    }) =>
      api<components["schemas"]["KnowledgeRow"]>("/api/knowledge", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
    },
  });
}

export function useUpdateKnowledge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      knowledgeId: number;
      title?: string;
      body?: string;
      kind?: string;
    }) =>
      api<components["schemas"]["KnowledgeRow"]>(
        `/api/knowledge/${vars.knowledgeId}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            title: vars.title,
            body: vars.body,
            kind: vars.kind,
          }),
        },
      ),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
      qc.invalidateQueries({ queryKey: ["knowledge", vars.knowledgeId] });
    },
  });
}

export function useDeleteKnowledge() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (knowledgeId: number) =>
      api<void>(`/api/knowledge/${knowledgeId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
    },
  });
}

export function useCreateKnowledgeLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      knowledgeId: number;
      from_type: string;
      from_id: string;
      to_type: string;
      to_id: string;
      relation?: string;
    }) =>
      api<components["schemas"]["KnowledgeLinkRow"]>(
        `/api/knowledge/${vars.knowledgeId}/links`,
        {
          method: "POST",
          body: JSON.stringify({
            from_type: vars.from_type,
            from_id: vars.from_id,
            to_type: vars.to_type,
            to_id: vars.to_id,
            relation: vars.relation ?? "related",
          }),
        },
      ),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["knowledge", vars.knowledgeId] });
    },
  });
}

export function useDeleteKnowledgeLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { linkId: number; knowledgeId: number }) =>
      api<void>(`/api/knowledge/links/${vars.linkId}`, { method: "DELETE" }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["knowledge", vars.knowledgeId] });
    },
  });
}

export function usePromoteHighlight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      highlight_id: number;
      title?: string;
      kind?: string;
    }) =>
      api<components["schemas"]["KnowledgeRow"]>(
        "/api/knowledge/from-highlight",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["knowledge"] });
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
