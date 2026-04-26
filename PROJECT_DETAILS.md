# AltData Reliability OS

## What this project is
AltData Reliability OS is an internal control plane for HFT-adjacent hedge funds that depend on alternative data. The system tracks whether incoming feeds and the derived features built from them are trustworthy enough for research and production use. It gives operators and researchers one place to inspect feed health, review degradation incidents, replay point-in-time feature states, and decide whether a feature should remain active, degrade gracefully, or be blocked.

## What changed in this phase
- Bootstrapped the monorepo layout with `apps/web`, `apps/api`, `services/ingest`, `services/scorer`, `packages/contracts`, and `infra/terraform`.
- Added the first FastAPI control-plane implementation with seeded overview, feed health, feature reliability, incidents, and replay endpoints.
- Added a scoring module that computes weighted trust scores and classifies feed state.
- Added synthetic ingestion connectors for three MVP feed classes.
- Replaced the default Next.js starter with a dark-mode dashboard shell, feed drill-down page, and incident replay page.
- Added Docker Compose for local infrastructure and Terraform scaffolding for AWS.
- Added the ADR that explains the Stitch-to-code workflow.

## Why these pieces exist
- `apps/web` exists to provide the operator-facing control plane.
- `apps/api` exists to expose a stable backend surface for feeds, incidents, replay, and health aggregation.
- `services/ingest` exists to model raw delivery intake and synthetic failure scenarios during local development.
- `services/scorer` exists to compute trust dimensions and translate them into operational status.
- `packages/contracts` exists to hold shared frontend-facing contract definitions.
- `infra/terraform` exists to capture the long-term AWS deployment shape instead of leaving infrastructure implicit.

## Verified design assets
- Google Stitch project: `projects/3546797177250251721`
- Dashboard screen: `projects/3546797177250251721/screens/d084e2e784534dfbac1a27034fc6ce42`
- Feed detail drill-down screen: `projects/3546797177250251721/screens/6ae1696353cb443cbecd3b5147974928`
- Incident management and replay screen: `projects/3546797177250251721/screens/c0a0ea2698ee4ea182da94d846904802`
- Design system asset: `assets/a5ad9344335845c2b46c091d096f3143`

## How the system works
1. Ingestion workers pull or receive alternative data deliveries from external vendors.
2. Raw deliveries are stored in object storage for replay, auditability, and forensic debugging.
3. Delivery metadata, feed definitions, and reliability history are persisted to Postgres.
4. Scoring workers compute freshness, completeness, schema stability, entity coverage, revision pressure, drift anomaly score, and a weighted trust score.
5. If a score breaches thresholds, an incident is created and attached to the impacted feed and features.
6. The control-plane API serves dashboards, drill-down views, incident workflows, and replay payloads.
7. The frontend visualizes those states in a dense dark-mode operating surface derived from Google Stitch concepts.

## Current architecture
- `apps/web`
  - Next.js App Router frontend
  - Tailwind CSS v4 styling
  - Framer Motion and Lightweight Charts for motion and telemetry
  - TanStack Table for incident list rendering
- `apps/api`
  - FastAPI control plane
  - Pydantic schemas
  - SQLAlchemy and Alembic declared for persistence and migration work
  - Seeded API responses for the MVP vertical slice
- `services/ingest`
  - Synthetic connectors for traffic proxy, footfall stream, and news/event feed classes
- `services/scorer`
  - Weighted trust score calculations and state classification
- `packages/contracts`
  - Shared TypeScript contract definitions consumed by the frontend
- `infra/terraform`
  - Initial AWS provider and VPC scaffolding

## Core data model
- `FeedDefinition`
  - Canonical description of a vendor feed, its SLA target, region, and status.
- `ReliabilitySnapshot`
  - Point-in-time trust dimensions and the weighted trust score that drives operational state.
- `FeatureDefinition`
  - Research-facing feature metadata mapped back to its source feed.
- `FeatureSnapshot`
  - Latest feature value, lineage, and associated reliability state.
- `IncidentRecord`
  - Operator-facing issue record with severity, workflow state, and impacted features.
- `ReplayResponse`
  - Point-in-time expected versus actual feature values with trust-state decisions.

## Local development
### Prerequisites
- Node.js 20 or 22 is recommended. The current scaffold also works on Node 21, but some packages emit engine warnings.
- Python 3.10+
- Docker Desktop for local infra services

### Run the web app
1. `cd apps/web`
2. `npm install`
3. `npm run dev`

### Run the API
1. From the repository root, install dependencies if needed:
   - `python -m pip install fastapi uvicorn pydantic sqlalchemy alembic httpx pytest`
2. Start the API from the repository root:
   - `python -m uvicorn apps.api.app.main:app --reload`

### Run local infrastructure
- `docker compose up -d`

## How to test
- Frontend lint:
  - `npm run lint:web`
- Frontend typecheck:
  - `npm run typecheck:web`
- API tests:
  - `npm run test:api`
- Scoring tests:
  - `npm run test:scorer`
- Combined verification:
  - `npm test`

## How to deploy
### Current deployment direction
- AWS is the production target.
- Terraform will provision networking, data stores, and service foundations.
- The intended runtime model is:
  - `apps/web` as the frontend service
  - `apps/api` as the control-plane service
  - `services/ingest` and `services/scorer` as workers or scheduled tasks

### Target AWS services
- VPC and subnets
- RDS Postgres
- S3
- MSK-compatible Kafka
- ECS/Fargate
- CloudWatch

## Researcher workflow
1. Researcher inspects a feature in the replay view.
2. They compare expected versus actual values during a degraded period.
3. They review the trust score and incident linkage.
4. They decide whether the feature should remain live, degrade in weight, or be blocked for that time window.

## Operator workflow
1. Operator watches the overview dashboard for trust deterioration.
2. They open a feed drill-down to inspect freshness, schema, and revisions.
3. They acknowledge and triage incidents from the incident ledger.
4. They use replay payloads to verify whether the issue contaminates downstream research features.

## Documentation rule
This file must always explain the project from scratch. Every major implementation phase should update:
- what changed
- why it exists
- how it works
- how to run it locally
- how to test it
- how to deploy it

## Next milestones
- Replace seeded API data with database-backed persistence and Alembic migrations.
- Add raw payload storage and replay-backed ingestion history.
- Implement live updates for dashboard refresh.
- Expand the frontend into full feed registry and configuration forms.
- Flesh out AWS modules for data, compute, secrets, and deployment pipelines.
