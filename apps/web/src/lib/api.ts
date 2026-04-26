import type { OverviewResponse } from "@contracts";

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

