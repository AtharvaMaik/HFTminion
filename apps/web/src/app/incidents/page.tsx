import { AppShell } from "@/components/app-shell";
import { IncidentsTable } from "@/components/incidents-table";
import { getIncidents, getReplay } from "@/lib/api";

export default async function IncidentsPage() {
  const [incidents, replay] = await Promise.all([
    getIncidents(),
    getReplay("feat-news-sentiment"),
  ]);
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
          <IncidentsTable incidents={incidents} />
        </section>

        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Point-in-Time Replay
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Expected vs actual feature payload
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                Expected
              </div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-emerald-100">
                {`sentiment_score: ${replay?.points.at(0)?.expected_value.toFixed(2) ?? "-0.22"}\nevent_group: "macro"\ntrust_state: "degrade"\nblocked: false`}
              </pre>
            </div>
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                Actual
              </div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-rose-100">
                {`sentiment_score: ${latestPoint?.actual_value.toFixed(2) ?? "null"}\nevent_group: ""\ntrust_state: "${latestPoint?.blocked ? "critical" : "healthy"}"\nblocked: ${latestPoint?.blocked ? "true" : "false"}`}
              </pre>
            </div>
          </div>
          <div className="mt-6 rounded-xl bg-cyan-400/8 p-4 text-sm text-cyan-50">
            Decision view: this feature would be {latestPoint?.blocked ? "blocked" : "passed"} for downstream research while the replay drift remains outside the trusted band.
          </div>
        </section>
      </div>
    </AppShell>
  );
}
