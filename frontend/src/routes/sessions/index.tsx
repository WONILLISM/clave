import { createFileRoute } from "@tanstack/react-router";
import { useSessions } from "~/api/queries";
import { SessionsTable } from "~/components/sessions/SessionsTable";

export const Route = createFileRoute("/sessions/")({
  component: SessionsPage,
});

function SessionsPage() {
  const { data, isPending, error } = useSessions({ limit: 200 });

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {isPending && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          불러오는 중…
        </div>
      )}
      {error && (
        <div className="px-6 py-12 text-center text-error">
          {String(error)}
        </div>
      )}
      {data && data.items.length === 0 && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          세션이 없습니다.
        </div>
      )}
      {data && data.items.length > 0 && (
        <SessionsTable sessions={data.items} />
      )}
    </div>
  );
}
