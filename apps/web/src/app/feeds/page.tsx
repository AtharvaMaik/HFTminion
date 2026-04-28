import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { getFeeds, getIncidents } from "@/lib/api";

export default async function FeedsIndexPage() {
  const [feeds, incidents] = await Promise.all([getFeeds(), getIncidents()]);
  const feedNameById = Object.fromEntries(feeds.map((feed) => [feed.id, feed.name]));

  return (
    <AppShell eyebrow="Feed Directory" title="All live public sources">
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Live Source Catalog
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Select a live public source
          </h2>
          <div className="mt-6 space-y-4">
            {feeds.map((feed) => (
              <Link
                key={feed.id}
                href={`/feeds/${feed.id}`}
                className="block rounded-xl bg-white/4 p-4 transition-colors hover:bg-white/8"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium text-cyan-100">{feed.name}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em] text-white/45">
                      {feed.vendor} / {feed.region}
                    </div>
                  </div>
                  <div className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-white/70">
                    {feed.status}
                  </div>
                </div>
                <div className="mt-4 grid gap-3 text-sm text-white/60 md:grid-cols-3">
                  <div>Type: {feed.feed_class.replaceAll("_", " ")}</div>
                  <div>SLA: {feed.freshness_sla_seconds}s</div>
                  <div>Coverage: {feed.coverage_target_pct}%</div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <aside className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Active Exceptions
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Incidents by live source
          </h2>
          <div className="mt-6 space-y-4">
            {incidents.map((incident) => (
              <div key={incident.id} className="rounded-xl bg-white/4 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-white/85">{incident.id}</div>
                  <div className="text-xs uppercase tracking-[0.18em] text-white/45">
                    {incident.severity}
                  </div>
                </div>
                <div className="mt-2 text-sm text-white/65">{incident.title}</div>
                <div className="mt-2 text-xs text-cyan-100">
                  {feedNameById[incident.feed_id] ?? incident.feed_id}
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
