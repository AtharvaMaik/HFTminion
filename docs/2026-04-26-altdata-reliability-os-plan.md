# AltData Reliability OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an industry-grade internal platform for HFT-adjacent hedge funds that ingests alternative data feeds, scores feature reliability, exposes a dark-mode operations UI, and prevents degraded data from contaminating research workflows.

**Architecture:** The system is a monorepo with a Next.js frontend, FastAPI control-plane API, worker services for ingestion and scoring, shared contracts, and AWS infrastructure managed with Terraform. Frontend design starts in Google Stitch for screen generation and design direction, then gets implemented in code with Tailwind CSS, shadcn/ui, Tremor, Lightweight Charts, TanStack Table, and Framer Motion.

**Tech Stack:** Next.js, TypeScript, Tailwind CSS, shadcn/ui, Tremor, TanStack Table, TanStack Query, Lightweight Charts, Framer Motion, FastAPI, Pydantic, SQLAlchemy, Alembic, Kafka-compatible broker, Prefect, Postgres, S3, Terraform, AWS ECS/RDS/MSK/CloudWatch.

---

## Summary
- Use AWS as the target production environment.
- Build a strong MVP vertical slice rather than a broad multi-product platform.
- Use Google Stitch as the frontend design accelerator and source of first-pass screen structure before code implementation.
- Maintain a root-level `PROJECT_DETAILS.md` throughout the project as the system explainer and operator/developer onboarding document.

## Frontend and Stitch Workflow
- Google Stitch is verified working for this project:
  - Stitch project created: `projects/3546797177250251721`
  - Dashboard screen generated successfully for the product
  - Generated screen asset: `projects/3546797177250251721/screens/d084e2e784534dfbac1a27034fc6ce42`
  - Generated design system asset: `assets/a5ad9344335845c2b46c091d096f3143`
- Frontend execution flow:
  - Start each major surface in Stitch with prompt-based screen generation.
  - Review generated layout, density, and dark-mode treatment.
  - Translate approved screens into coded components in `apps/web`.
  - Keep Stitch as design source and coded UI as implementation source of truth.
- Required frontend surfaces:
  - Dashboard overview
  - Feed detail drill-down
  - Feature detail and reliability replay
  - Incident management table
  - System configuration and feed registry forms
- UI rules:
  - Dark mode by default
  - Tailwind CSS for styling tokens and utility layout
  - shadcn/ui for layout primitives, dialogs, sheets, tabs, dropdowns, command UI
  - Tremor for KPI cards and quick health summaries
  - Lightweight Charts for live market-style telemetry
  - TanStack Table styled with shadcn for incidents and feed history
  - Framer Motion for smooth route transitions, panel reveals, filter transitions, and subtle alert pulses

## Key Interfaces and Core Data Model
- Shared contracts:
  - `FeedDefinition`
  - `FeedDelivery`
  - `FeatureDefinition`
  - `FeatureSnapshot`
  - `ReliabilitySnapshot`
  - `IncidentRecord`
  - `VendorRevisionEvent`
- API endpoints:
  - `POST /api/v1/feeds`
  - `GET /api/v1/feeds`
  - `GET /api/v1/feeds/:id/health`
  - `POST /api/v1/ingestion-runs`
  - `GET /api/v1/features`
  - `GET /api/v1/features/:id/reliability`
  - `GET /api/v1/incidents`
  - `POST /api/v1/incidents/:id/acknowledge`
  - `GET /api/v1/metrics/overview`
  - `GET /api/v1/replay/:featureId`
- Reliability score dimensions:
  - freshness
  - completeness
  - schema stability
  - entity coverage
  - revision rate
  - drift anomaly score
  - weighted trust score

## End-to-End Delivery Plan
### Phase 0: Planning and project scaffolding
- [ ] Create the monorepo folder layout:
  - `apps/web`
  - `apps/api`
  - `services/ingest`
  - `services/scorer`
  - `packages/contracts`
  - `infra/terraform`
  - `docs`
- [ ] Create `PROJECT_DETAILS.md` and seed sections for architecture, services, data flow, local setup, testing, deployment, and glossary.
- [ ] Save Google Stitch identifiers and screen references into `PROJECT_DETAILS.md`.
- [ ] Create an ADR for the Stitch-to-code UI workflow.

### Phase 1: Monorepo bootstrap
- [ ] Initialize `apps/web` with Next.js App Router and TypeScript.
- [ ] Initialize `apps/api` with FastAPI, Pydantic, SQLAlchemy, Alembic.
- [ ] Initialize shared contract package for request/response and event schemas.
- [ ] Add root lint, typecheck, formatting, test, and CI scripts.
- [ ] Add Docker Compose for local Postgres, object storage emulator, Kafka-compatible broker, and Grafana stack.

### Phase 2: Design system and frontend shell
- [ ] Generate or refine the dashboard and drill-down screens in Stitch before coding them.
- [ ] Implement dark theme tokens in Tailwind.
- [ ] Install and configure shadcn/ui primitives.
- [ ] Build the app shell: sidebar, top status bar, layout grid, modal/sheet patterns.
- [ ] Add motion primitives with Framer Motion.
- [ ] Implement overview page skeleton from approved Stitch screens.

### Phase 3: Persistence and contracts
- [ ] Define database tables for feeds, deliveries, features, reliability snapshots, incidents, revisions, and audit metadata.
- [ ] Write initial Alembic migrations.
- [ ] Implement shared contract exports for frontend/backend reuse.
- [ ] Document every model and relationship in `PROJECT_DETAILS.md`.

### Phase 4: Ingestion pipeline
- [ ] Build feed connectors for three MVP classes:
  - web/app traffic proxy
  - store/footfall-style event stream
  - news/event feed
- [ ] Land raw payloads into object storage.
- [ ] Track ingestion runs and delivery metadata in Postgres.
- [ ] Inject realistic failure cases:
  - stale delivery
  - null bursts
  - schema mutation
  - delayed backfill revision

### Phase 5: Reliability scoring engine
- [ ] Implement freshness, completeness, revision-rate, and coverage scoring jobs.
- [ ] Add drift and change-point detection on feature distributions.
- [ ] Compute and persist weighted trust scores.
- [ ] Trigger incidents when thresholds are breached.
- [ ] Expose historical reliability time series for charting and replay.

### Phase 6: Control-plane API
- [ ] Implement feed, feature, metrics, incident, and replay endpoints.
- [ ] Add filtering, pagination, and health aggregation responses.
- [ ] Add SSE or websocket updates for live dashboard refresh.
- [ ] Add API-level validation and error shape consistency.

### Phase 7: Product UI implementation
- [ ] Implement top KPI cards with Tremor.
- [ ] Implement real-time reliability panel with Lightweight Charts.
- [ ] Implement incidents table with TanStack Table and shadcn filters.
- [ ] Implement feed and feature drill-down pages using Stitch-generated layouts as the visual baseline.
- [ ] Implement slide-over incident detail and acknowledgment flow.

### Phase 8: Research trust UX
- [ ] Build point-in-time replay for feature values and trust state.
- [ ] Show feature lineage from feed to derived feature to impacted incident.
- [ ] Add “would this feature be blocked” decision view for degraded periods.
- [ ] Document researcher workflow in `PROJECT_DETAILS.md`.

### Phase 9: Observability and operations
- [ ] Add OpenTelemetry to API and workers.
- [ ] Add metrics, traces, logs, service health checks, and job status dashboards.
- [ ] Add CloudWatch alarms and local Grafana dashboards for:
  - ingestion lag
  - stale feeds
  - incident spikes
  - worker failure rate
- [ ] Write runbook sections in `PROJECT_DETAILS.md` for operator response.

### Phase 10: AWS deployment
- [ ] Provision VPC, subnets, security groups, RDS Postgres, S3, MSK Serverless, ECS/Fargate services, secrets, and CloudWatch.
- [ ] Deploy `apps/web` and `apps/api` as separate services behind an ALB or equivalent routing setup.
- [ ] Deploy ingestion/scoring workers as ECS services or scheduled tasks.
- [ ] Configure CI/CD for:
  - test and typecheck
  - Docker image builds
  - image publish
  - Terraform validate/plan/apply
  - environment deployment

### Phase 11: Hardening and demo readiness
- [ ] Seed realistic data and synthetic failure scenarios.
- [ ] Run smoke tests against deployed frontend and API.
- [ ] Run an end-to-end demo:
  - degrade a feed
  - generate an incident
  - lower feature trust
  - inspect replay
  - acknowledge resolution
- [ ] Finalize `PROJECT_DETAILS.md` as the canonical explain-from-scratch guide.

## Test Plan
- Unit tests:
  - score calculations
  - contract validation
  - API serialization
- Integration tests:
  - ingestion writes raw payloads and metadata
  - scoring persists reliability snapshots
  - incidents trigger correctly
  - replay returns point-in-time-correct responses
- Frontend tests:
  - dashboard KPIs render correct states
  - charts handle loading and degraded states
  - incident table filters and sorts correctly
  - sheets and modals open/close with correct data
- End-to-end tests:
  - feed degradation appears in dashboard
  - incident can be acknowledged
  - feature drill-down shows impacted trust score and replay
- Deployment checks:
  - Terraform validation
  - image build success
  - API/web smoke tests
  - synthetic alert alarm test

## Assumptions
- AWS is the default production target.
- Authentication stays minimal in v1 because this is an internal platform MVP.
- The coded frontend remains the implementation source of truth even though Stitch is used heavily for screen ideation and layout direction.
- `PROJECT_DETAILS.md` must be updated during every major phase and treated as required project documentation, not optional notes.
