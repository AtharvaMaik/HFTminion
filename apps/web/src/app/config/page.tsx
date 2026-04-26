import { AppShell } from "@/components/app-shell";
import { getFeeds, getFeatures, getIncidents } from "@/lib/api";

export default async function ConfigPage() {
  const [feeds, features, incidents] = await Promise.all([
    getFeeds(),
    getFeatures(),
    getIncidents(),
  ]);

  return (
    <AppShell eyebrow="Operator Config" title="Pipeline topology and controls">
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Feed Registry
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Live integration surfaces
          </h2>
          <div className="mt-6 space-y-4">
            {feeds.map((feed) => (
              <div key={feed.id} className="rounded-xl bg-white/4 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium text-cyan-100">{feed.name}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em] text-white/45">
                      {feed.vendor} / {feed.region} / {feed.feed_class}
                    </div>
                  </div>
                  <div className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-white/70">
                    {feed.status}
                  </div>
                </div>
                <div className="mt-4 grid gap-3 text-sm text-white/65 md:grid-cols-2">
                  <div>SLA: {feed.freshness_sla_seconds}s</div>
                  <div>Coverage target: {feed.coverage_target_pct}%</div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className="space-y-6">
          <section className="panel rounded-2xl p-5">
            <div className="text-xs uppercase tracking-[0.28em] text-white/45">
              Feature Routing
            </div>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
              Downstream dependencies
            </h2>
            <div className="mt-6 space-y-3">
              {features.map((feature) => (
                <div key={feature.id} className="rounded-xl bg-white/4 p-4">
                  <div className="font-medium text-cyan-100">{feature.name}</div>
                  <div className="mt-1 text-sm text-white/60">{feature.description}</div>
                  <div className="mt-2 font-[family-name:var(--font-mono)] text-xs text-white/45">
                    {feature.feed_id} {"->"} {feature.owner}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel rounded-2xl p-5">
            <div className="text-xs uppercase tracking-[0.28em] text-white/45">
              Current Controls
            </div>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
              Incident-driven policy state
            </h2>
            <div className="mt-6 space-y-3">
              {incidents.map((incident) => (
                <div key={incident.id} className="rounded-xl bg-white/4 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-white/85">{incident.id}</span>
                    <span className="text-xs uppercase tracking-[0.18em] text-white/45">
                      {incident.acknowledged ? "acknowledged" : "pending"}
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-white/60">{incident.title}</div>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
