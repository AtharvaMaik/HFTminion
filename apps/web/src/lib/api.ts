import type {
  FeatureDefinition,
  FeedDefinition,
  FeedHealth,
  IncidentRecord,
  OverviewResponse,
  ReplayResponse,
} from "@contracts";

import { fallbackOverview } from "./mock-data";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getOverview(): Promise<OverviewResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/metrics/overview`, {
      next: { revalidate: 30 },
    });
    if (!response.ok) {
      throw new Error(`API error ${response.status}`);
    }
    return (await response.json()) as OverviewResponse;
  } catch {
    return fallbackOverview;
  }
}

async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      next: { revalidate: 30 },
    });
    if (!response.ok) {
      throw new Error(`API error ${response.status}`);
    }
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export async function getFeeds(): Promise<FeedDefinition[]> {
  return apiGet("/api/v1/feeds", []);
}

export async function getFeedHealth(feedId: string): Promise<FeedHealth | null> {
  return apiGet(`/api/v1/feeds/${feedId}/health`, null);
}

export async function getIncidents(): Promise<IncidentRecord[]> {
  return apiGet("/api/v1/incidents", fallbackOverview.incidents);
}

export async function acknowledgeIncident(incidentId: string): Promise<IncidentRecord | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/acknowledge`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({ acknowledged: true }),
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error(`API error ${response.status}`);
    }
    return (await response.json()) as IncidentRecord;
  } catch {
    return null;
  }
}

export async function getFeatures(): Promise<FeatureDefinition[]> {
  return apiGet("/api/v1/features", []);
}

export async function getReplay(featureId: string): Promise<ReplayResponse | null> {
  return apiGet(`/api/v1/replay/${featureId}`, null);
}

