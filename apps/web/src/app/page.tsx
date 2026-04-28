import { AppShell } from "@/components/app-shell";
import { OverviewLivePanel } from "@/components/overview-live-panel";
import { getFeeds, getOverview } from "@/lib/api";

export default async function Home() {
  const [overview, feeds] = await Promise.all([getOverview(), getFeeds()]);

  return (
    <AppShell eyebrow="Dashboard Overview" title="Reliability command center">
      <OverviewLivePanel initialOverview={overview} initialFeeds={feeds} />
    </AppShell>
  );
}

