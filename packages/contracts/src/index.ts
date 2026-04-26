export type ReliabilityStatus = "healthy" | "warning" | "critical";

export type FeedDefinition = {
  id: string;
  name: string;
  vendor: string;
  region: string;
  feed_class: "traffic_proxy" | "footfall_stream" | "news_event_feed";
  freshness_sla_seconds: number;
  coverage_target_pct: number;
  status: ReliabilityStatus;
};

export type ReliabilitySnapshot = {
  timestamp: string;
  freshness: number;
  completeness: number;
  schema_stability: number;
  entity_coverage: number;
  revision_rate: number;
  drift_anomaly_score: number;
  weighted_trust_score: number;
  status: ReliabilityStatus;
};

export type IncidentRecord = {
  id: string;
  title: string;
  feed_id: string;
  severity: ReliabilityStatus;
  status: "triage" | "investigating" | "resolved";
  started_at: string;
  acknowledged: boolean;
  summary: string;
  impacted_features: string[];
};

export type OverviewMetric = {
  label: string;
  value: string;
  delta: string;
  tone: "cyan" | "emerald" | "amber" | "red";
};

export type OverviewResponse = {
  metrics: OverviewMetric[];
  feeds_by_status: Record<string, number>;
  trust_timeseries: Array<[string, number]>;
  incidents: IncidentRecord[];
};

