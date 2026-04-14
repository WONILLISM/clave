/**
 * TanStack Query thin hooks.
 * 이번 라운드는 헬스체크 하나. W2 에서 projects/sessions 추가.
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

// schema.ts 가 생성되기 전에도 컴파일 되도록 inline 타입.
// gen:api 후엔 paths 에서 끌어다 쓰도록 교체 예정.
export interface HealthResponse {
  status: string;
  db_path: string;
  indexed_sessions: number;
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api<HealthResponse>("/api/health"),
    refetchInterval: 5_000,
  });
}
