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

export type FeedHealth = {
  feed: FeedDefinition;
  latest_snapshot: ReliabilitySnapshot;
  latency_seconds: number;
  schema_version: string;
  incident_count: number;
};

export type FeatureDefinition = {
  id: string;
  name: string;
  feed_id: string;
  description: string;
  owner: string;
};

export type FeatureSnapshot = {
  feature_id: string;
  feature_name: string;
  latest_value: number;
  reliability: ReliabilitySnapshot;
  lineage: string[];
};

export type ReplayPoint = {
  timestamp: string;
  expected_value: number;
  actual_value: number;
  trust_score: number;
  blocked: boolean;
};

export type ReplayResponse = {
  feature_id: string;
  feature_name: string;
  points: ReplayPoint[];
};

