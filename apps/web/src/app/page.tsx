import { AppShell } from "@/components/app-shell";
import { IncidentsTable } from "@/components/incidents-table";
import { MetricCard } from "@/components/metric-card";
import { ReliabilityChart } from "@/components/reliability-chart";
import { getOverview } from "@/lib/api";

export default async function Home() {
  const overview = await getOverview();

  return (
    <AppShell eyebrow="Dashboard Overview" title="Reliability command center">
      <section className="grid gap-4 xl:grid-cols-4">
        {overview.metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <div className="panel rounded-2xl p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.28em] text-white/45">
                Trust Score Trend
              </div>
              <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
                24h weighted trust stability
              </h2>
            </div>
            <div className="rounded-full bg-cyan-400/10 px-3 py-1 font-[family-name:var(--font-mono)] text-sm text-cyan-100">
              LIVE PIPELINE
            </div>
          </div>
          <ReliabilityChart data={overview.trust_timeseries} />
        </div>

        <div className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Fleet Status
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Feed health distribution
          </h2>
          <div className="mt-8 space-y-4">
            {Object.entries(overview.feeds_by_status).map(([status, count]) => (
              <div key={status} className="rounded-xl bg-white/4 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-[0.24em] text-white/45">
                    {status}
                  </span>
                  <span className="font-[family-name:var(--font-mono)] text-lg text-white/85">
                    {count}
                  </span>
                </div>
                <div className="mt-3 h-2 rounded-full bg-white/6">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-cyan-300 to-cyan-500"
                    style={{ width: `${Math.min(100, count * 10)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div>
          <div className="mb-4">
            <div className="text-xs uppercase tracking-[0.28em] text-white/45">
              Active & Historical Incidents
            </div>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
              Operator queue with replay handoff
            </h2>
          </div>
          <IncidentsTable incidents={overview.incidents} />
        </div>

        <div className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Stitch Baseline
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Generated surface references
          </h2>
          <div className="mt-6 space-y-4 text-sm text-white/70">
            <div className="rounded-xl bg-white/4 p-4">
              <div className="font-medium text-cyan-100">Dashboard screen</div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-xs">
                d084e2e784534dfbac1a27034fc6ce42
              </div>
            </div>
            <div className="rounded-xl bg-white/4 p-4">
              <div className="font-medium text-cyan-100">Feed detail drill-down</div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-xs">
                6ae1696353cb443cbecd3b5147974928
              </div>
            </div>
            <div className="rounded-xl bg-white/4 p-4">
              <div className="font-medium text-cyan-100">Incident replay surface</div>
              <div className="mt-2 font-[family-name:var(--font-mono)] text-xs">
                c0a0ea2698ee4ea182da94d846904802
              </div>
            </div>
          </div>
        </div>
      </section>
    </AppShell>
  );
}

