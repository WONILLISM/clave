import { createFileRoute } from "@tanstack/react-router";
import { useKnowledge } from "~/api/queries";
import { KnowledgeDetail } from "~/components/knowledge/KnowledgeDetail";
import { BookOpen } from "lucide-react";

export const Route = createFileRoute("/knowledge/$knowledgeId")({
  component: KnowledgeDetailPage,
});

function KnowledgeDetailPage() {
  const { knowledgeId } = Route.useParams();
  const id = Number(knowledgeId);
  const { data, isPending, error } = useKnowledge(id);

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center text-outline">
        불러오는 중...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3">
        <BookOpen size={32} className="text-outline-variant/30" />
        <p className="text-sm text-on-surface-variant">
          지식 항목을 찾을 수 없습니다.
        </p>
      </div>
    );
  }

  return <KnowledgeDetail data={data} />;
}
