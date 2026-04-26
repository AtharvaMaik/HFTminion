import { AppShell } from "@/components/app-shell";

type FeedPageProps = {
  params: Promise<{ feedId: string }>;
};

export default async function FeedPage({ params }: FeedPageProps) {
  const { feedId } = await params;

  return (
    <AppShell eyebrow="Feed Drill-down" title={`Feed detail: ${feedId}`}>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Schema + Freshness
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Delivery stability and replay context
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {[
              ["Freshness", "39 sec", "SLA 45 sec"],
              ["Schema version", "2.4.0", "shifted 2h ago"],
              ["Revision pressure", "1.8x", "baseline 0.5x"],
            ].map(([label, value, meta]) => (
              <div key={label} className="rounded-xl bg-white/4 p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                  {label}
                </div>
                <div className="mt-2 font-[family-name:var(--font-display)] text-2xl text-cyan-100">
                  {value}
                </div>
                <div className="mt-2 text-sm text-white/55">{meta}</div>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-2xl bg-[#060e20] p-4 font-[family-name:var(--font-mono)] text-sm text-cyan-100">
            {`{\n  "feed": "${feedId}",\n  "payload_status": "replayed",\n  "fields_missing": ["sentiment_score", "event_group"],\n  "revision_window": "T-07m",\n  "action": "degrade research usage"\n}`}
          </div>
        </section>

        <aside className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Incident Sidebar
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Recent interventions
          </h2>
          <div className="mt-6 space-y-4">
            {[
              ["Critical", "Latency breach crossed stale threshold"],
              ["Warning", "Null burst detected in vendor backfill"],
              ["Resolved", "Schema mutation mapped by normalizer"],
            ].map(([level, summary]) => (
              <div key={summary} className="rounded-xl bg-white/4 p-4">
                <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                  {level}
                </div>
                <div className="mt-2 text-sm text-white/75">{summary}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}

