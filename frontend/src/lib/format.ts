import { formatDistanceToNow, parseISO } from "date-fns";
import { ko } from "date-fns/locale";

/** ISO 날짜 → "3분 전" 스타일 상대 시각 */
export function timeAgo(iso: string): string {
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true, locale: ko });
  } catch {
    return iso;
  }
}

/** decoded_cwd 에서 부모 디렉터리 추출. ~/work/foo → ~/work */
export function parentDir(cwd: string): string {
  const idx = cwd.lastIndexOf("/");
  return idx > 0 ? cwd.slice(0, idx) : cwd;
}

/** decoded_cwd 에서 마지막 세그먼트. ~/work/foo → foo */
export function baseName(cwd: string): string {
  const idx = cwd.lastIndexOf("/");
  return idx >= 0 ? cwd.slice(idx + 1) : cwd;
}

/** /Users/<user>/... → ~/... 축약 */
export function shortenPath(path: string): string {
  return path.replace(/^\/Users\/[^/]+/, "~");
}

/** 바이트 수 → 사람이 읽기 좋은 단위 문자열. null/undefined 이면 "—" 반환. */
export function formatBytes(n: number | null | undefined): string {
  if (n == null) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}
