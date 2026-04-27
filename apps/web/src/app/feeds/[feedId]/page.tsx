import { AppShell } from "@/components/app-shell";
import { FeedLivePanel } from "@/components/feed-live-panel";
import { getFeedHealth, getFeatures, getIncidents } from "@/lib/api";

type FeedPageProps = {
  params: Promise<{ feedId: string }>;
};

export default async function FeedPage({ params }: FeedPageProps) {
  const { feedId } = await params;
  const [health, features, incidents] = await Promise.all([
    getFeedHealth(feedId),
    getFeatures(),
    getIncidents(),
  ]);

  const feedFeatures = features.filter((feature) => feature.feed_id === feedId);

  return (
    <AppShell eyebrow="Feed Drill-down" title={`Feed detail: ${feedId}`}>
      <FeedLivePanel
        feedId={feedId}
        feedFeatures={feedFeatures}
        initialHealth={health}
        initialIncidents={incidents}
      />
    </AppShell>
  );
}

