import type { OverviewResponse } from "@contracts";

const fallbackNow = Date.now();

export const fallbackOverview: OverviewResponse = {
  metrics: [
    { label: "Tracked feeds", value: "3", delta: "live public sources", tone: "cyan" },
    { label: "Healthy trust", value: "83.7%", delta: "+4.2 pts", tone: "emerald" },
    { label: "Active incidents", value: "2", delta: "-1 since open", tone: "amber" },
    { label: "Blocked signals", value: "1", delta: "Headline Velocity", tone: "red" },
  ],
  feeds_by_status: { healthy: 1, warning: 1, critical: 1 },
  trust_timeseries: [
    [new Date(fallbackNow - 55 * 60 * 1000).toISOString(), 71],
    [new Date(fallbackNow - 50 * 60 * 1000).toISOString(), 74],
    [new Date(fallbackNow - 45 * 60 * 1000).toISOString(), 77],
    [new Date(fallbackNow - 40 * 60 * 1000).toISOString(), 79],
    [new Date(fallbackNow - 35 * 60 * 1000).toISOString(), 83],
    [new Date(fallbackNow - 30 * 60 * 1000).toISOString(), 87],
    [new Date(fallbackNow - 25 * 60 * 1000).toISOString(), 84],
    [new Date(fallbackNow - 20 * 60 * 1000).toISOString(), 81],
    [new Date(fallbackNow - 15 * 60 * 1000).toISOString(), 85],
    [new Date(fallbackNow - 10 * 60 * 1000).toISOString(), 89],
    [new Date(fallbackNow - 5 * 60 * 1000).toISOString(), 91],
    [new Date(fallbackNow).toISOString(), 93],
  ],
  incidents: [
    {
      id: "inc-live-feed-economic-calendar",
      title: "Revision burst exceeded daily baseline",
      feed_id: "feed-economic-calendar",
      severity: "warning",
      status: "investigating",
      started_at: new Date().toISOString(),
      acknowledged: true,
      summary: "Vendor backfill revisions spiked 3.6x above the expected rate.",
      impacted_features: ["Economic Event Pressure"],
    },
    {
      id: "inc-live-feed-public-news",
      title: "Macro event feed staleness breach",
      feed_id: "feed-public-news",
      severity: "critical",
      status: "triage",
      started_at: new Date().toISOString(),
      acknowledged: false,
      summary: "Latency breached the 45 second SLA for 7 consecutive windows.",
      impacted_features: ["Headline Velocity"],
    },
  ],
};

