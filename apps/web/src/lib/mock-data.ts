import type { OverviewResponse } from "@contracts";

export const fallbackOverview: OverviewResponse = {
  metrics: [
    { label: "Tracked feeds", value: "3", delta: "live public sources", tone: "cyan" },
    { label: "Healthy trust", value: "83.7%", delta: "+4.2 pts", tone: "emerald" },
    { label: "Active incidents", value: "2", delta: "-1 since open", tone: "amber" },
    { label: "Blocked signals", value: "1", delta: "Headline Velocity", tone: "red" },
  ],
  feeds_by_status: { healthy: 1, warning: 1, critical: 1 },
  trust_timeseries: [
    ["08:00", 71],
    ["09:00", 74],
    ["10:00", 77],
    ["11:00", 79],
    ["12:00", 83],
    ["13:00", 87],
    ["14:00", 84],
    ["15:00", 81],
    ["16:00", 85],
    ["17:00", 89],
    ["18:00", 91],
    ["19:00", 93],
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

