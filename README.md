# HFTminion

AltData Reliability OS is a control plane for alternative-data operations in research and trading environments. It helps a team ingest external feeds, score how trustworthy those feeds and derived features are, detect incidents early, and decide whether a feature should stay live, degrade, or be blocked before it contaminates downstream models or research.

This repository currently contains an MVP vertical slice:
- A Next.js operations UI for dashboard, feed drill-down, and incident replay
- A FastAPI control-plane API with seeded or database-backed feed, feature, and incident data
- A scoring module for weighted trust computation
- Live public-source connectors for market, news, and macro signal monitoring
- Docker and Terraform scaffolding for local dependencies and AWS direction
- A Vercel multi-service deployment path for sharing the web UI and API on one domain

## What It Does

The product is designed around one operational question:

"Can we trust this alternative-data feature right now?"

To answer that, the system models the full path from vendor delivery to research feature:
- Vendor feeds are defined with expected SLA and coverage targets
- Deliveries are tracked for freshness, completeness, schema stability, revision behavior, and drift
- A weighted trust score is computed per feed or feature snapshot
- Incidents are raised when trust falls below thresholds
- Operators and researchers can inspect replay data and incident lineage in the UI

The included UI surfaces are:
- Dashboard overview
  - KPI cards
  - trust trend graph
  - fleet health distribution
  - incident queue
- Feed drill-down
  - freshness and schema context
  - replay payload summary
  - incident sidebar
- Incident replay view
  - incident ledger
  - expected vs actual payload comparison
  - blocked-feature decision framing

## Repository Layout

```text
apps/
  web/              Next.js frontend
  api/              FastAPI control-plane API
services/
  ingest/           Synthetic feed connector layer
  scorer/           Reliability scoring logic
packages/
  contracts/        Shared TypeScript-facing contracts
infra/
  terraform/        AWS infrastructure direction
docs/               ADRs and planning documents
```

## Core Concepts

### FeedDefinition
Describes an external vendor feed: vendor, region, feed class, SLA, target coverage, and current state.

### ReliabilitySnapshot
Captures trust dimensions at a point in time:
- freshness
- completeness
- schema stability
- entity coverage
- revision rate
- drift anomaly score
- weighted trust score

### FeatureSnapshot
Connects a research-facing feature back to its originating feed and current reliability state.

### IncidentRecord
Represents a human-operable issue record tied to a feed or degraded feature.

### ReplayResponse
Shows expected vs actual values and whether the system would block the feature during that interval.

## Local Development

### Prerequisites
- Node.js 20 or 22 recommended
- Python 3.10+
- Docker Desktop recommended for local infra

### Install Dependencies

Frontend:

```powershell
cd apps/web
npm install
```

Backend:

```powershell
python -m pip install fastapi uvicorn pydantic sqlalchemy alembic httpx pytest
```

### Run the Web App

From repository root:

```powershell
npm run dev:web
```

The UI is served at:

```text
http://127.0.0.1:3000
```

### Run the API

From repository root:

```powershell
python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is served at:

```text
http://127.0.0.1:8000
```

### Run the API in Database Mode

The API can now boot in a persistent database-backed mode instead of relying only on in-memory seeded state.

```powershell
$env:DATA_MODE="database"
$env:DATABASE_URL="postgresql+psycopg://altdata:altdata@localhost:15432/altdata"
python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

When `DATA_MODE=database`, startup will:
- create the persistence tables
- seed the current demo records into the database once
- serve feeds, incidents, replay, and overview data from durable storage

### Run the API in Live Vendor Mode

Live mode now supports three public no-auth sources:
- `feed-binance-agg` using Binance US public spot market data for `BTCUSDT`
- `feed-public-news` using public RSS headlines
- `feed-economic-calendar` using Federal Reserve press-release RSS as the live macro/event cadence source

```powershell
$env:DATA_MODE="live"
$env:LIVE_VENDOR_SYMBOL="BTCUSDT"
python -m uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

In `DATA_MODE=live`:
- `/api/v1/feeds`, `/api/v1/features`, `/api/v1/incidents`, and `/api/v1/metrics/overview` expose only the live-backed records
- `feed-binance-agg` refreshes from the live market data path
- `feed-public-news` refreshes from the configured public RSS source
- `feed-economic-calendar` refreshes from the configured Federal Reserve RSS source
- `feat-order-imbalance`, `feat-headline-velocity`, and `feat-economic-event-pressure` are derived from those live sources
- live snapshots, replay points, ingestion runs, and live incidents are persisted into the existing tables

Optional settings:

```text
LIVE_VENDOR_FEED_ID=feed-binance-agg
LIVE_VENDOR_SYMBOL=BTCUSDT
LIVE_VENDOR_BASE_URL=https://api.binance.us
LIVE_PUBLIC_NEWS_RSS_URL=https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en
LIVE_ECONOMIC_CALENDAR_URL=https://www.federalreserve.gov/feeds/press_all.xml
LIVE_REFRESH_WINDOW_SECONDS=30
LIVE_VENDOR_TIMEOUT_SECONDS=5
```

The default hosted configuration uses `https://api.binance.us` because Vercel's US runtime can receive HTTP 451 from `api.binance.com`. The macro source defaults to the Federal Reserve RSS feed because it is fetchable from automated server-side clients, unlike some government calendar endpoints that block bot traffic.

### Run Local Infra

```powershell
docker compose up -d
```

Services defined today:
- Postgres
- MinIO
- Redpanda
- Prometheus
- Grafana

## Verification

### Frontend

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
```

### Backend

```powershell
npm run test:api
npm run test:scorer
```

### Deployment Build Check

```powershell
npm run build:web
```

### Manual Smoke Checks

API:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/api/v1/metrics/overview
Invoke-WebRequest http://127.0.0.1:8000/api/v1/feeds
```

UI:
- `/`
- `/feeds/feed-public-news`
- `/feeds/feed-economic-calendar`
- `/incidents`

## Deployment

### Shared Web Deployment

The repo is configured for a shared Vercel deployment using the root [vercel.json](./vercel.json), with:
- `apps/web` served as the primary Next.js frontend
- `apps/api/app/main.py` served as the FastAPI backend

The frontend now resolves API requests in this order:
1. `NEXT_PUBLIC_API_BASE_URL` if explicitly set
2. the current Vercel deployment URL in hosted environments
3. `http://127.0.0.1:8000` for local development

That means the deployed UI can call the co-hosted API without pointing at localhost.

### Vercel Setup

One-time project setup:

```powershell
npm install -g vercel
vercel
```

If the Vercel project is not linked yet, run the command from the repository root so Vercel picks up the root `vercel.json`.

For production:

```powershell
vercel --prod
```

### Recommended Environment Variables

For local or hosted database-backed API mode, set:

```text
DATA_MODE=database
DATABASE_URL=postgresql+psycopg://altdata:altdata@localhost:15432/altdata
```

If you want the frontend to target an external API instead of the co-hosted service, set:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-api-host.example.com
```

For a hosted live demo on Vercel, set at least:

```text
DATA_MODE=live
LIVE_VENDOR_SYMBOL=BTCUSDT
```

If you override the live source URLs, prefer endpoints that are reachable from automated server-side clients in your deployment region. The default app config uses `https://api.binance.us` for market data and `https://www.federalreserve.gov/feeds/press_all.xml` for macro/event cadence because both are fetchable from the shared Vercel deployment.

If `DATABASE_URL` is not set on Vercel, the API falls back to `/tmp/altdata.db`, which is good enough for a shareable live demo but not durable across cold starts.

## How To Integrate This Into a Real Pipeline

The current repo now has a truthful live public-source slice in `DATA_MODE=live`, while `seeded` and `database` modes still exist for local/demo workflows. The architecture is already shaped for a deeper real event-driven data pipeline.

### 1. Ingestion Layer

In a production pipeline, replace the synthetic `services/ingest` connector layer with real vendor adapters.

Typical sources:
- SFTP drops
- REST vendor APIs
- websocket/streaming feeds
- Kafka or Redpanda topics
- object-store dropzones

Production flow:
1. Pull or receive raw vendor payloads
2. Store raw payloads in object storage
3. Emit normalized delivery metadata into Postgres and/or a stream
4. Track delivery timestamps, schema versions, null rates, and revision markers

Recommended integrations:
- Airflow or Prefect for scheduled pulls
- Kafka/Redpanda for event propagation
- S3 for raw payload archive
- dbt or feature pipelines downstream for derived features

### 2. Reliability Scoring Layer

The current `services/scorer` module already expresses the trust model in code. In a real pipeline:
- run scorers on every new delivery window
- persist each `ReliabilitySnapshot`
- compute both feed-level and feature-level trust
- trigger incident creation when thresholds are breached

Typical implementation options:
- Scheduled batch scoring every N minutes
- Event-driven scoring on each successful ingestion completion
- Hybrid approach:
  - event-driven freshness checks
  - scheduled drift and coverage checks

Recommended persisted outputs:
- `feed_deliveries`
- `reliability_snapshots`
- `feature_snapshots`
- `vendor_revision_events`
- `incidents`

### 3. Incident and Replay Layer

For real operations, incident generation should not stay inside the UI or only inside the API seed layer.

A practical design is:
1. Scoring service writes a degraded snapshot
2. Threshold evaluator determines state transition
3. Incident service creates or updates an incident record
4. Notification hooks fan out to Slack, PagerDuty, email, or internal alerting
5. Replay service reconstructs point-in-time context from raw storage plus normalized snapshots

The replay path should be able to answer:
- what vendor payload did we receive?
- what normalized feature value did we compute?
- what trust score existed at that timestamp?
- would the feature have been blocked for research or live trading?

### 4. API Integration

This API should sit between operational data stores and the UI.

In a real deployment:
- replace seeded in-memory data with repository/service layers
- back all list/detail endpoints with Postgres queries
- add pagination, filtering, and auth
- add SSE or WebSocket updates for live dashboard refresh
- expose replay data from object storage plus snapshot tables

The web app already expects a base API URL via:

```text
NEXT_PUBLIC_API_BASE_URL
```

That makes it straightforward to point the UI at:
- local API
- staging API
- production API

### 5. Frontend Integration in a Real Workflow

The frontend is intended to be the operator and researcher interface, not the source of truth.

Use it as:
- the place operators watch feed health and incidents
- the place researchers inspect degraded periods before trusting a feature
- the place incident triage and replay decisions happen

In a real production setup, the UI should be connected to:
- SSO / identity provider
- role-based access
- incident workflow notes
- lineage links to upstream datasets and downstream models

### 6. Suggested Production Architecture

Recommended target architecture:
- Ingestion workers on ECS/Fargate or Kubernetes
- Redpanda/Kafka for feed event propagation
- S3 for raw payload archive
- Postgres/RDS for metadata and trust snapshots
- FastAPI service for control-plane API
- Next.js app for operator UI
- Prometheus/Grafana/CloudWatch for observability

Data path:

```text
Vendor Feed
  -> Ingestion Worker
  -> Raw Payload Archive (S3)
  -> Delivery Metadata Store (Postgres)
  -> Scoring Worker
  -> Reliability Snapshots + Incidents
  -> Control-Plane API
  -> Web UI / Alerts / Research Consumers
```

### 7. What Still Needs to Be Added for a Real Pipeline

Before this becomes production-ready, add:
- durable hosted database infrastructure instead of ephemeral fallback storage
- broader vendor coverage beyond the current three public sources
- source-specific parsing, retry, and alerting hardening for each connector
- object-store replay retrieval
- auth and audit logging
- incident workflow persistence
- live streaming updates
- threshold configuration by feed or feature class
- observability instrumentation and alarms
- CI/CD and environment promotion

## AWS Direction

Terraform scaffolding is included to show the intended AWS deployment direction.

The expected production targets are:
- VPC and subnets
- RDS Postgres
- S3
- MSK-compatible streaming
- ECS/Fargate services
- CloudWatch

## Current Limitations

This repository is currently an MVP scaffold and operator demo baseline.

Important limitations:
- live mode currently covers only three public sources, not commercial vendor integrations
- seeded and database demo modes still exist for local/demo workflows
- Docker infra can require local port hygiene
- live ingestion is polling-based, not a full production pipeline
- hosted persistence can still fall back to ephemeral storage if `DATABASE_URL` is not configured
- replay is still illustrative, not reconstructed from archived payloads

## Why This Exists

Alternative data fails in subtle ways:
- feeds go stale
- vendors revise history
- schemas mutate
- coverage collapses silently
- downstream features drift before anyone notices

This project exists to make those failures visible before they become trading or research mistakes.
