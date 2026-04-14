import type { LucideIcon } from "lucide-react";
import { Terminal, FolderOpen, Pin, Tag } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
}

function StatCard({ icon: Icon, label, value }: StatCardProps) {
  return (
    <div className="flex flex-col gap-1 rounded-sm border border-outline-variant/20 bg-surface-container-low px-4 py-3">
      <div className="flex items-center gap-2 text-on-surface-variant/60">
        <Icon size={14} />
        <span className="text-2xs uppercase tracking-wider">{label}</span>
      </div>
      <span className="font-mono text-xl font-bold text-on-surface">
        {value}
      </span>
    </div>
  );
}

interface Props {
  totalSessions: number;
  totalProjects: number;
  pinnedSessions: number;
  totalTags: number;
}

export function StatCards({
  totalSessions,
  totalProjects,
  pinnedSessions,
  totalTags,
}: Props) {
  return (
    <div className="grid grid-cols-4 gap-3">
      <StatCard icon={Terminal} label="총 세션" value={totalSessions} />
      <StatCard icon={FolderOpen} label="프로젝트" value={totalProjects} />
      <StatCard icon={Pin} label="고정 세션" value={pinnedSessions} />
      <StatCard icon={Tag} label="태그" value={totalTags} />
    </div>
  );
}
