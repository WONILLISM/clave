/**
 * 백엔드 호출용 fetch 래퍼.
 *
 * - dev: vite proxy 가 `/api` 를 `127.0.0.1:8765` 로 흘려줌 → baseUrl 비움.
 * - prod (W2+): 동일 origin 정적 서빙 가정 → 역시 baseUrl 비움.
 *
 * 응답 타입은 `paths["/api/..."]["get"]["responses"]["200"]["content"]["application/json"]`
 * 형식으로 schema.ts 에서 끌어 쓴다.
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API ${status} ${statusText}`);
    this.name = "ApiError";
  }
}

export async function api<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // ignore — 응답이 JSON 이 아닐 수도
    }
    throw new ApiError(res.status, res.statusText, body);
  }

  // 204 같은 빈 응답 케어
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
