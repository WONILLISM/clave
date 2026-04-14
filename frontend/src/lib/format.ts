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
