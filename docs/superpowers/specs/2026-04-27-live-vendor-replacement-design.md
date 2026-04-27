# Live Vendor Replacement Design

Date: 2026-04-27

## Goal

Replace the remaining demo vendors, demo feed names, demo feature names, and demo incidents with real public no-auth data sources so that `DATA_MODE=live` exposes only truthful live-backed surfaces.

The end state is a live public data reliability console with no seeded vendor identities shown in production live mode.

## Problem

The current live deployment mixes one real live feed (`feed-binance-agg`) with two demo feeds (`feed-footfall-east`, `feed-global-news`). This creates UI and product confusion:

- incident rows look real even when they are seeded demo records
- feed and vendor labels imply integrations that do not exist
- dashboard metrics combine real and synthetic states
- the app does not clearly distinguish between "demo mode" and "live mode"

This must be corrected by making `DATA_MODE=live` an honest all-live mode.

## Scope

This design covers:

- replacing the two remaining demo feeds with public no-auth live sources
- renaming feed, feature, and vendor identities to match the real sources
- removing seeded/demo feed exposure from live mode
- generating incidents only from live refresh/trust outcomes in live mode
- updating dashboard and detail surfaces so counts and labels reflect actual live data

This design does not cover:

- paid commercial vendor integrations
- auth-protected APIs
- object-storage-backed replay reconstruction
- streaming/websocket ingestion
- multi-user workflow/audit systems

## Target Live Feed Set

### 1. Market Microstructure Feed

- Feed id: `feed-binance-agg`
- Vendor label: `Binance US`
- Source type: public spot market REST
- Base URL: `https://api.binance.us`
- Existing feature: `feat-order-imbalance`
- Feature label: `Order Imbalance Regime`

This feed already exists and remains the baseline live market source.

### 2. Global News Feed

- Replace `feed-global-news`
- Replace vendor label `EventPulse`
- Source type: public RSS/JSON news feed
- New feed label should explicitly reflect the actual chosen source
- Feature rename: from synthetic "Macro News Shock Sentiment" to a truthful measure such as:
  - `Headline Velocity Pulse`, or
  - `News Event Pressure Index`

The system should measure what is actually available from the source:

- headline arrival freshness
- article count velocity
- delivery continuity
- title duplication / anomaly rate

The system must not imply proprietary sentiment analysis unless such analysis is actually implemented.

### 3. Macro/Economic Activity Feed

- Replace `feed-footfall-east`
- Replace vendor label `StreetLayer`
- Source type: public macro/economic releases or economic calendar style feed
- New feed label should reflect the real source, not footfall
- Feature rename: from "Store Visit Intent Delta" to something truthful such as:
  - `Economic Release Activity Index`, or
  - `Macro Event Pressure`

The system should measure what is actually available:

- release/event freshness
- release cadence continuity
- event volume versus recent baseline
- source availability / schema continuity

The system must not retain the footfall framing.

## Product Behavior by Mode

### Seeded Mode

Seeded mode may continue to expose demo feeds and incidents for local/product demo purposes.

### Database Mode

Database mode may continue to expose seeded demo data as a persistent local/demo baseline.

### Live Mode

Live mode must expose only live-backed feeds, live-backed features, and live-generated incidents.

Rules for live mode:

- do not expose seeded feed identities
- do not expose seeded incidents
- do not expose seeded feature snapshots for removed demo feeds
- dashboard counts and trends must be derived from the actual live feed set
- if a live connector fails, surface that as a live incident for the corresponding feed

## Architecture Changes

### Current State

Today the backend has:

- a seeded dataset in `apps/api/app/data.py`
- DB seeding in `apps/api/app/seed.py`
- a single-feed live service in `apps/api/app/services/live_vendor.py`
- live refresh only for `feed-binance-agg`

### Proposed State

Replace the single-feed live implementation with a connector registry and multi-feed refresh engine.

### Connector Interface

Each live connector should define:

- `feed_id`
- source/vendor display metadata
- fetch logic
- trust input derivation logic
- feature derivation logic
- replay derivation logic
- live incident summary rules

Each connector returns normalized feed output compatible with:

- `FeedSnapshotModel`
- `FeatureSnapshotModel`
- `ReplayPointModel`
- `IncidentModel`

### Multi-Feed Refresh Service

`LiveFeedRefreshService` should evolve into a multi-feed service that:

- knows the set of live-backed feed ids
- refreshes a single feed by id
- refreshes all live feeds for overview/dashboard pulls when needed
- decides whether a feed snapshot is still current using per-feed recency checks
- emits incidents for failures and trust threshold breaches

### Live Mode Filtering

In `CurrentStateService` and repository-backed API responses:

- list endpoints should filter to live-backed feed ids in `DATA_MODE=live`
- feature endpoints should filter to live-backed feature ids in `DATA_MODE=live`
- incident endpoints should only show incidents tied to live-backed feeds in `DATA_MODE=live`

Seeded rows may still physically exist in the same database, but live-mode API responses must not expose them.

## Data Model and Naming

The existing tables are sufficient for the next slice:

- `feeds`
- `features`
- `feed_snapshots`
- `feature_snapshots`
- `incidents`
- `incident_events`
- `replay_points`
- `ingestion_runs`

The primary change is the record identities and labels stored in those tables.

### Feed Naming Requirements

- feed ids should remain stable once chosen
- display names must match the real source
- vendor labels must match the real source
- regions must reflect actual deployment/source context where meaningful

### Feature Naming Requirements

- feature names must describe actual derived metrics
- lineage must name real source components/endpoints
- no synthetic-normalizer naming unless such a transform actually exists

## API Contract

The current public endpoints remain:

- `GET /api/v1/feeds`
- `GET /api/v1/feeds/{feedId}/health`
- `GET /api/v1/features`
- `GET /api/v1/features/{featureId}/reliability`
- `GET /api/v1/incidents`
- `POST /api/v1/incidents/{incidentId}/acknowledge`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/replay/{featureId}`
- `POST /api/v1/ingestion-runs`

The contract shape stays stable. The meaning of returned records changes:

- in live mode, returned records are all live-backed
- counts and trend summaries must be computed from the live-backed set
- incidents in live mode must come from live connector failures or trust degradation

## UI Changes

Layout changes should be minimal. Truthfulness changes are required.

### Required UI Updates

- replace demo vendor/feed names with real source names
- remove fake fleet numbers such as "18 tracked feeds" if not true
- remove synthetic trend values if they are not computed from live state
- ensure incident rows describe actual live issues
- ensure replay labels match actual features and sources

### Optional UI Improvements

If the rename work causes awkward layouts or visual mismatches, use Google Stitch to improve the affected surfaces while preserving the current information architecture.

This should be limited to:

- feed cards
- dashboard KPI copy
- feed detail headings / metadata blocks
- incident table labels

The project should not undergo a broad visual redesign as part of this migration.

## Replay Semantics

Replay remains illustrative but must be honest.

For each live-backed feature:

- expected values should come from the connector's baseline/reference logic
- actual values should come from the fetched source data
- trust scores should derive from the same reliability model used for feed snapshots
- blocked state should reflect actual trust threshold results

If a feed cannot support meaningful replay, the connector may emit a simplified recent-point replay, but the UI copy must not imply archived forensic reconstruction.

## Incident Rules

In live mode, incidents should only come from:

- connector fetch failures
- freshness breaches
- trust threshold breaches
- schema or source continuity failures

Seeded incident ids such as `inc-1042` and `inc-1043` must not appear in live mode.

Each live incident should include:

- feed id
- truthful title
- severity
- workflow status
- summary from the actual failure/degradation
- impacted live features

## Deployment and Runtime

For Vercel-hosted live mode:

- continue using no-auth public APIs only
- prefer US-reachable sources
- keep `cache: no-store` behavior for live frontend polling
- retain `/tmp/altdata.db` fallback only as temporary hosted persistence unless a real database is configured

The app must continue to run with:

- `DATA_MODE=live`
- no paid credentials required

## Implementation Order

### Phase 1: Honest Live-Only Mode

- filter live-mode API responses to live-backed records only
- remove seeded/demo incident exposure in live mode
- replace fake dashboard counts and trend summaries with values computed from live-backed feeds
- ensure UI labels match the current live-backed set

### Phase 2: Add Public News Connector

- implement a real public news connector
- create truthful feed and feature records
- derive live snapshots, incidents, and replay points
- wire into dashboard and feed detail pages

### Phase 3: Add Public Macro/Economic Connector

- implement a real public macro/economic connector
- create truthful feed and feature records
- derive live snapshots, incidents, and replay points
- wire into dashboard and feed detail pages

### Phase 4: Remove Demo Identity Leakage

- remove old demo feed/feature naming from live-mode paths
- ensure no seeded demo incidents surface in live mode
- update docs and hosted deployment defaults

## Testing

Add or update tests for:

- live-mode feed filtering
- live-mode incident filtering
- live dashboard metric derivation from live-backed feeds only
- connector-specific snapshot derivation
- connector failure -> live incident creation
- feature replay generation for each live-backed source
- UI polling surfaces rendering live-backed names and values

## Risks

- public no-auth sources can change format or rate-limit unexpectedly
- some public sources may not support rich replay semantics
- replacing the fake footfall domain with a real macro domain will require copy changes throughout the UI
- trend/KPI areas currently rely partly on synthetic summaries and will need real derivation logic

## Recommendation

Proceed with approach 1:

- replace the demo vendors with real public sources
- rename the feeds/features/vendors to match the sources
- make `DATA_MODE=live` a truthful live-only mode

This is the smallest path that removes product confusion while preserving the overall architecture and UI structure.
