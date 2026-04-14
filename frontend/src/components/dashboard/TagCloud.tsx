import type { TagListItem } from "~/api/queries";

interface Props {
  tags: TagListItem[];
}

export function TagCloud({ tags }: Props) {
  return (
    <div className="rounded-sm border border-outline-variant/20 bg-surface-container-low">
      <div className="px-4 py-3">
        <h2 className="text-sm font-semibold text-on-surface">태그</h2>
      </div>
      <div className="flex flex-wrap gap-2 px-4 pb-4">
        {tags.map((t) => (
          <span
            key={t.tag_id}
            className="inline-flex items-center gap-1.5 rounded-full border border-outline-variant/20 bg-surface-container px-2.5 py-1 text-2xs text-on-surface-variant"
          >
            {t.color && (
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: t.color }}
              />
            )}
            <span className="text-primary/70">{t.name}</span>
          </span>
        ))}
        {tags.length === 0 && (
          <span className="text-sm text-on-surface-variant/40">태그 없음</span>
        )}
      </div>
    </div>
  );
}
