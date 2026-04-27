import { AppShell } from "@/components/app-shell";
import { OverviewLivePanel } from "@/components/overview-live-panel";
import { getOverview } from "@/lib/api";

export default async function Home() {
  const overview = await getOverview();

  return (
    <AppShell eyebrow="Dashboard Overview" title="Reliability command center">
      <OverviewLivePanel initialOverview={overview} />
    </AppShell>
  );
}

