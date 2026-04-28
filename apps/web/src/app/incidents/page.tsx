import { AppShell } from "@/components/app-shell";
import { IncidentsTable } from "@/components/incidents-table";
import { getFeeds, getIncidents, getReplay } from "@/lib/api";

export default async function IncidentsPage() {
  const [feeds, incidents, replay] = await Promise.all([
    getFeeds(),
    getIncidents(),
    getReplay("feat-headline-velocity"),
  ]);
  const feedNameById = Object.fromEntries(feeds.map((feed) => [feed.id, feed.name]));
  const latestPoint = replay?.points.at(-1);

  return (
    <AppShell eyebrow="Incident Replay" title="Historical and active incident analysis">
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section>
          <div className="mb-4">
            <div className="text-xs uppercase tracking-[0.28em] text-white/45">
              Queue
            </div>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
              Triage-ready incident ledger
            </h2>
          </div>
          <IncidentsTable incidents={incidents} feedNameById={feedNameById} />
        </section>

        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Point-in-Time Replay
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Expected vs observed live signal
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                Expected
              </div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-emerald-100">
                {`feature_id: "${replay?.feature_id ?? "feat-headline-velocity"}"\nfeature_name: "${replay?.feature_name ?? "Headline Velocity"}"\nexpected_value: ${replay?.points.at(0)?.expected_value.toFixed(2) ?? "0.00"}\nblocked: false`}
              </pre>
            </div>
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                Actual
              </div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-rose-100">
                {`feature_id: "${replay?.feature_id ?? "feat-headline-velocity"}"\nfeature_name: "${replay?.feature_name ?? "Headline Velocity"}"\nactual_value: ${latestPoint?.actual_value.toFixed(2) ?? "null"}\nblocked: ${latestPoint?.blocked ? "true" : "false"}`}
              </pre>
            </div>
          </div>
          <div className="mt-6 rounded-xl bg-cyan-400/8 p-4 text-sm text-cyan-50">
            Decision view: this live signal would be {latestPoint?.blocked ? "blocked" : "passed"} for downstream consumers while replay drift remains outside the trusted band.
          </div>
        </section>
      </div>
    </AppShell>
  );
}
