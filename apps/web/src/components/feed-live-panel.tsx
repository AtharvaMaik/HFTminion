"use client";

import type { FeatureDefinition, FeedHealth, IncidentRecord } from "@contracts";

import { getFeedHealthLive, getIncidentsLive } from "@/lib/api";
import { useLiveQuery } from "@/lib/use-live-query";

type FeedLivePanelProps = {
  feedId: string;
  feedFeatures: FeatureDefinition[];
  initialHealth: FeedHealth | null;
  initialIncidents: IncidentRecord[];
};

export function FeedLivePanel({
  feedId,
  feedFeatures,
  initialHealth,
  initialIncidents,
}: FeedLivePanelProps) {
  const { data: health, isRefreshing } = useLiveQuery({
    initialData: initialHealth,
    query: () => getFeedHealthLive(feedId),
  });
  const { data: incidents } = useLiveQuery({
    initialData: initialIncidents,
    query: getIncidentsLive,
  });

  const relatedIncidents = incidents.filter((incident) => incident.feed_id === feedId);
  const latestSnapshot = health?.latest_snapshot;

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <section className="panel rounded-2xl p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-white/45">
              Source Delivery + Freshness
            </div>
            <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
              Delivery stability and live signal context
            </h2>
          </div>
          <div className="rounded-full bg-cyan-400/10 px-3 py-1 font-[family-name:var(--font-mono)] text-xs text-cyan-100">
            {isRefreshing ? "SYNCING" : "LIVE 5S"}
          </div>
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[
            [
              "Freshness",
              `${health?.latency_seconds ?? "--"} sec`,
              `SLA ${health?.feed.freshness_sla_seconds ?? "--"} sec`,
            ],
            [
              "Schema version",
              health?.schema_version ?? "unknown",
              `${health?.incident_count ?? 0} linked incidents`,
            ],
            [
              "Weighted trust",
              latestSnapshot ? `${latestSnapshot.weighted_trust_score.toFixed(1)}` : "--",
              `state ${latestSnapshot?.status ?? "unknown"}`,
            ],
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
          {`{\n  "feed_id": "${feedId}",\n  "source_name": "${health?.feed.name ?? "unknown"}",\n  "source_vendor": "${health?.feed.vendor ?? "unknown"}",\n  "region": "${health?.feed.region ?? "unknown"}",\n  "status": "${latestSnapshot?.status ?? "unknown"}",\n  "weighted_trust_score": ${latestSnapshot?.weighted_trust_score?.toFixed(1) ?? "null"},\n  "signals": [${feedFeatures.map((feature) => `"${feature.name}"`).join(", ")}]\n}`}
        </div>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl bg-white/4 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-white/45">
              Reliability vector
            </div>
            <div className="mt-3 space-y-2 text-sm text-white/65">
              <div>Freshness: {latestSnapshot?.freshness ?? "--"}</div>
              <div>Completeness: {latestSnapshot?.completeness ?? "--"}</div>
              <div>Schema stability: {latestSnapshot?.schema_stability ?? "--"}</div>
              <div>Entity coverage: {latestSnapshot?.entity_coverage ?? "--"}</div>
            </div>
          </div>
          <div className="rounded-xl bg-white/4 p-4">
            <div className="text-xs uppercase tracking-[0.22em] text-white/45">
              Derived live signals
            </div>
            <div className="mt-3 space-y-2 text-sm text-white/65">
              {feedFeatures.map((feature) => (
                <div key={feature.id}>
                  <div className="text-cyan-100">{feature.name}</div>
                  <div className="text-xs text-white/45">{feature.owner}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <aside className="panel rounded-2xl p-5">
        <div className="text-xs uppercase tracking-[0.28em] text-white/45">
          Source Incidents
        </div>
        <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl">
          Recent interventions
        </h2>
        <div className="mt-6 space-y-4">
          {relatedIncidents.map((incident) => (
            <div key={incident.id} className="rounded-xl bg-white/4 p-4">
              <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                {incident.severity}
              </div>
              <div className="mt-2 text-sm text-white/75">{incident.title}</div>
              <div className="mt-2 text-xs text-white/45">
                {incident.acknowledged ? "Acknowledged" : "Awaiting acknowledgment"}
              </div>
            </div>
          ))}
          {relatedIncidents.length === 0 ? (
            <div className="rounded-xl bg-white/4 p-4 text-sm text-white/55">
              No active incidents are currently linked to this feed.
            </div>
          ) : null}
        </div>
      </aside>
    </div>
  );
}
