import { AppShell } from "@/components/app-shell";
import { getReplay } from "@/lib/api";

const featureId = "feat-news-sentiment";

export default async function ReplayPage() {
  const replay = await getReplay(featureId);

  const latestPoint = replay?.points.at(-1);
  const maxTrust = Math.max(...(replay?.points.map((point) => point.trust_score) ?? [100]));

  return (
    <AppShell eyebrow="Replay Studio" title="Point-in-time feature replay">
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Feature Reconstruction
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            {replay?.feature_name ?? "Replay unavailable"}
          </h2>
          <div className="mt-6 space-y-3">
            {(replay?.points ?? []).map((point) => {
              const delta = (point.expected_value - point.actual_value).toFixed(2);
              const width = `${Math.max(18, (point.trust_score / maxTrust) * 100)}%`;
              return (
                <div key={point.timestamp} className="rounded-xl bg-white/4 p-4">
                  <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em] text-white/45">
                    <span>{new Date(point.timestamp).toLocaleTimeString()}</span>
                    <span>{point.blocked ? "blocked" : "flowing"}</span>
                  </div>
                  <div className="mt-3 grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
                    <div>
                      <div className="text-sm text-white/70">
                        Expected {point.expected_value.toFixed(2)} / Actual {point.actual_value.toFixed(2)}
                      </div>
                      <div className="mt-1 text-xs text-white/45">Delta {delta}</div>
                      <div className="mt-3 h-2 rounded-full bg-white/6">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300"
                          style={{ width }}
                        />
                      </div>
                    </div>
                    <div className="font-[family-name:var(--font-mono)] text-lg text-cyan-100">
                      {point.trust_score.toFixed(0)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <aside className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Decision Snapshot
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Expected vs actual outcome
          </h2>
          <div className="mt-6 grid gap-4">
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">Expected</div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-emerald-100">
                {`feature_id: "${replay?.feature_id ?? featureId}"\ntrust_state: "degrade"\nblocked: false\npath: normalizer.v2 -> research`}
              </pre>
            </div>
            <div className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">Actual</div>
              <pre className="mt-3 whitespace-pre-wrap font-[family-name:var(--font-mono)] text-xs text-rose-100">
                {`feature_id: "${replay?.feature_id ?? featureId}"\ntrust_state: "${latestPoint?.blocked ? "critical" : "healthy"}"\nblocked: ${latestPoint?.blocked ? "true" : "false"}\npath: replay quarantine`}
              </pre>
            </div>
            <div className="rounded-xl bg-cyan-400/8 p-4 text-sm text-cyan-50">
              Replay confirms whether the feature should stay blocked while upstream freshness and schema issues are still active.
            </div>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
