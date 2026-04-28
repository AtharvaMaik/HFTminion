"use client";

import type { FeedDefinition, OverviewResponse } from "@contracts";
import Link from "next/link";

import { getFeedsLive, getOverviewLive } from "@/lib/api";
import { useLiveQuery } from "@/lib/use-live-query";

import { IncidentsTable } from "./incidents-table";
import { MetricCard } from "./metric-card";
import { ReliabilityChart } from "./reliability-chart";

export function OverviewLivePanel({
  initialOverview,
  initialFeeds,
}: {
  initialOverview: OverviewResponse;
  initialFeeds: FeedDefinition[];
}) {
  const { data: overview, isRefreshing } = useLiveQuery({
    initialData: initialOverview,
    query: getOverviewLive,
  });
  const { data: feeds } = useLiveQuery({
    initialData: initialFeeds,
    query: getFeedsLive,
  });
  const feedNameById = Object.fromEntries(feeds.map((feed) => [feed.id, feed.name]));
  const metrics = overview.metrics.map((metric) => {
    if (metric.label === "Tracked feeds") {
      return { ...metric, value: String(feeds.length), delta: "live public sources" };
    }
    if (metric.label === "Blocked features") {
      return { ...metric, label: "Blocked signals", delta: "live signal reliability" };
    }
    return metric;
  });

  return (
    <>
      <section className="grid gap-4 xl:grid-cols-4">
        {metrics.map((metric) => (
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
              {isRefreshing ? "SYNCING" : "LIVE 5S"}
            </div>
          </div>
          <ReliabilityChart data={overview.trust_timeseries} />
        </div>

        <div className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Live Source Status
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            Health across {feeds.length} live public sources
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
          <IncidentsTable incidents={overview.incidents} feedNameById={feedNameById} />
        </div>

        <div className="panel rounded-2xl p-5">
          <div className="text-xs uppercase tracking-[0.28em] text-white/45">
            Live Source Roster
          </div>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
            The public sources currently tracked
          </h2>
          <div className="mt-6 space-y-4 text-sm text-white/70">
            {feeds.map((feed) => (
              <Link
                key={feed.id}
                href={`/feeds/${feed.id}`}
                className="block rounded-xl bg-white/4 p-4 transition-colors hover:bg-white/8"
              >
                <div className="font-medium text-cyan-100">{feed.name}</div>
                <div className="mt-2 text-xs uppercase tracking-[0.18em] text-white/45">
                  {feed.vendor} / {feed.region}
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-white/55">
                  <span>{feed.feed_class.replaceAll("_", " ")}</span>
                  <span className="uppercase tracking-[0.18em] text-white/70">{feed.status}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
