import { createFileRoute } from "@tanstack/react-router";
import { useHealth } from "~/api/queries";

export const Route = createFileRoute("/")({
  component: IndexPage,
});

function IndexPage() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8 px-6 py-10">
      <HealthCard />
      <TokenSampler />
    </div>
  );
}

function HealthCard() {
  const { data, error, isPending } = useHealth();

  const dotColor = error
    ? "bg-error"
    : isPending
      ? "bg-on-surface-variant"
      : "bg-primary";
  const stateLabel = error ? "FAIL" : isPending ? "…" : "OK";

  return (
    <section className="rounded-md bg-surface-container p-6">
      <header className="mb-4 flex items-center gap-3">
        <span
          className={`inline-block h-2 w-2 rounded-full ${dotColor}`}
          aria-hidden
        />
        <h2 className="text-md font-medium tracking-tight">Backend Health</h2>
        <span className="ml-auto font-mono text-2xs uppercase tracking-widest text-on-surface-variant">
          {stateLabel}
        </span>
      </header>
      <pre className="overflow-x-auto rounded-sm bg-surface-container-lowest p-4 font-mono text-sm leading-relaxed text-on-surface">
        {error
          ? String(error)
          : isPending
            ? "loading…"
            : JSON.stringify(data, null, 2)}
      </pre>
    </section>
  );
}

function TokenSampler() {
  return (
    <section className="rounded-md bg-surface-container p-6">
      <h2 className="mb-4 text-md font-medium tracking-tight">Design Tokens</h2>

      <div className="mb-6">
        <p className="mb-2 font-mono text-2xs uppercase tracking-widest text-on-surface-variant">
          Surface Tier
        </p>
        <div className="grid grid-cols-4 gap-2">
          {[
            { name: "background", className: "bg-background" },
            { name: "container-low", className: "bg-surface-container-low" },
            { name: "container", className: "bg-surface-container" },
            { name: "container-high", className: "bg-surface-container-high" },
          ].map((s) => (
            <div
              key={s.name}
              className={`flex h-20 items-end rounded-sm border border-outline-variant/20 p-2 ${s.className}`}
            >
              <span className="font-mono text-2xs text-on-surface-variant">
                {s.name}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <p className="mb-2 font-mono text-2xs uppercase tracking-widest text-on-surface-variant">
          Accent
        </p>
        <div className="flex flex-wrap gap-2">
          {[
            { name: "primary", className: "bg-primary text-on-primary" },
            {
              name: "secondary",
              className: "bg-secondary-container text-on-secondary-container",
            },
            { name: "tertiary", className: "bg-tertiary text-on-tertiary" },
            {
              name: "error",
              className: "bg-error-container text-on-error-container",
            },
          ].map((c) => (
            <span
              key={c.name}
              className={`rounded-xs px-3 py-1 font-mono text-xs ${c.className}`}
            >
              {c.name}
            </span>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 font-mono text-2xs uppercase tracking-widest text-on-surface-variant">
          Typography
        </p>
        <div className="space-y-1">
          <p className="font-body text-2xl font-semibold tracking-tight">
            Inter · Display 28 — 잔잔한 정밀
          </p>
          <p className="text-md text-on-surface">
            Inter body — 본문 14px, 1.4 line-height
          </p>
          <p className="font-mono text-base text-on-surface-variant">
            JetBrains Mono · 81f3a7c4-b2cd-4f9a-9d12-...
          </p>
        </div>
      </div>
    </section>
  );
}
