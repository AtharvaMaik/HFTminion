# Live Vendor Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace demo vendors in `DATA_MODE=live` with truthful live public sources, expose only live-backed records in the API/UI, and add real public news plus macro/economic connectors.

**Architecture:** Keep the existing FastAPI + Next.js contract, but evolve the backend from a single Binance-specific live service into a connector registry with live-mode filtering. The frontend continues to use the same routes while labels, counts, incidents, and replay data become derived from only live-backed feeds.

**Tech Stack:** FastAPI, SQLAlchemy, Next.js App Router, TypeScript, pytest, public no-auth HTTP APIs, Vercel deployment

---

### Task 1: Lock live-mode filtering behavior in backend tests

**Files:**
- Modify: `apps/api/tests/test_api.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Add these tests near the existing live-mode tests:

```python
def test_live_mode_lists_only_live_backed_feeds(live_client: TestClient):
    response = live_client.get("/api/v1/feeds")
    assert response.status_code == 200
    body = response.json()
    assert [feed["id"] for feed in body] == [
        "feed-binance-agg",
        "feed-public-news",
        "feed-economic-calendar",
    ]


def test_live_mode_hides_seeded_demo_incidents(live_client: TestClient):
    response = live_client.get("/api/v1/incidents")
    assert response.status_code == 200
    body = response.json()
    assert all(item["id"] not in {"inc-1042", "inc-1043"} for item in body)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py -v
```

Expected: FAIL because live mode still includes seeded/demo feed and incident records.

- [ ] **Step 3: Write minimal implementation**

Update the test fixture so live mode stubs can support three live feeds instead of just Binance. Extend the test stub data to return realistic live ids for:

- `feed-binance-agg`
- `feed-public-news`
- `feed-economic-calendar`

Do not change production code yet; only prepare fixture coverage required for later tasks.

- [ ] **Step 4: Run test to verify it still fails for the right reason**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py -v
```

Expected: FAIL specifically on live list/filter assertions, not on broken test fixtures.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/tests/test_api.py
git commit -m "test: add live-mode filtering coverage"
```

### Task 2: Introduce live feed registry and source metadata

**Files:**
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/app/data.py`
- Create: `apps/api/app/services/live_registry.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add a unit-style assertion in `apps/api/tests/test_api.py`:

```python
from app.services.live_registry import LIVE_FEED_IDS


def test_live_registry_declares_all_live_feed_ids():
    assert LIVE_FEED_IDS == [
        "feed-binance-agg",
        "feed-public-news",
        "feed-economic-calendar",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_registry_declares_all_live_feed_ids -v
```

Expected: FAIL with import error because `live_registry.py` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `apps/api/app/services/live_registry.py` with:

```python
from __future__ import annotations

LIVE_FEED_IDS = [
    "feed-binance-agg",
    "feed-public-news",
    "feed-economic-calendar",
]

LIVE_FEATURE_IDS = [
    "feat-order-imbalance",
    "feat-headline-velocity",
    "feat-economic-event-pressure",
]
```

Update `apps/api/app/data.py` seeded definitions so the non-Binance feed and feature ids/names become truthful:

- `feed-global-news` -> `feed-public-news`
- `EventPulse` -> real source placeholder display label used in live mode design
- `feat-news-sentiment` -> `feat-headline-velocity`
- `feed-footfall-east` -> `feed-economic-calendar`
- `StreetLayer` -> real macro source placeholder display label
- `feat-store-intent` -> `feat-economic-event-pressure`

Do not remove seeded mode data yet; only rename the records.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_registry_declares_all_live_feed_ids -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/data.py apps/api/app/services/live_registry.py apps/api/tests/test_api.py apps/api/app/config.py
git commit -m "feat: add live registry and truthful source ids"
```

### Task 3: Generalize the live connector service interface

**Files:**
- Modify: `apps/api/app/services/live_vendor.py`
- Create: `apps/api/app/services/live_connectors.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add this test:

```python
def test_live_mode_feature_lineage_comes_from_connector(live_client: TestClient):
    response = live_client.get("/api/v1/features/feat-headline-velocity/reliability")
    assert response.status_code == 200
    body = response.json()
    assert body["lineage"][0].startswith("source:")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_mode_feature_lineage_comes_from_connector -v
```

Expected: FAIL because only the Binance-specific connector exists.

- [ ] **Step 3: Write minimal implementation**

Create `apps/api/app/services/live_connectors.py` with a connector protocol and a registry function:

```python
from __future__ import annotations

from typing import Protocol


class LiveConnector(Protocol):
    feed_id: str
    feature_id: str

    def fetch_snapshot(self): ...


def get_live_connectors():
    return {}
```

Refactor `live_vendor.py`:

- keep Binance logic in a `BinanceSpotConnector` class
- rename hardcoded `LIVE_FEATURE_ID` handling to per-connector fields
- prepare service methods to resolve a connector by `feed_id`

The implementation can still only fully execute Binance at this step, but the service API must no longer assume a single feed forever.

- [ ] **Step 4: Run the targeted test to verify the failure becomes an expected “not implemented” gap**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_mode_feature_lineage_comes_from_connector -v
```

Expected: still FAIL, but now because the extra live connectors are not registered yet, not because the service is structurally hardcoded to Binance.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/live_vendor.py apps/api/app/services/live_connectors.py apps/api/tests/test_api.py
git commit -m "refactor: prepare multi-connector live service"
```

### Task 4: Implement public news connector

**Files:**
- Modify: `apps/api/app/services/live_connectors.py`
- Modify: `apps/api/app/services/live_vendor.py`
- Modify: `apps/api/app/config.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add a mocked connector test:

```python
def test_live_news_feed_health_uses_real_source_shape(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-public-news/health")
    assert response.status_code == 200
    body = response.json()
    assert body["feed"]["id"] == "feed-public-news"
    assert body["schema_version"].startswith("rss-")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_news_feed_health_uses_real_source_shape -v
```

Expected: FAIL because the news connector is not implemented.

- [ ] **Step 3: Write minimal implementation**

In `live_connectors.py`, add a public RSS connector class:

- use `httpx` to fetch a public RSS/Atom endpoint
- derive:
  - freshness from latest item publish time
  - completeness from item parse success
  - schema stability from parse continuity
  - feature value from headline count / recent rate
- emit lineage like:

```python
[
    "source:public-news-rss",
    "rss:item-count",
    "feat-headline-velocity",
]
```

Register the connector in the live registry.

- [ ] **Step 4: Run targeted test to verify it passes**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_news_feed_health_uses_real_source_shape -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/live_connectors.py apps/api/app/services/live_vendor.py apps/api/app/config.py apps/api/tests/test_api.py
git commit -m "feat: add public news live connector"
```

### Task 5: Implement public macro/economic connector

**Files:**
- Modify: `apps/api/app/services/live_connectors.py`
- Modify: `apps/api/app/services/live_vendor.py`
- Modify: `apps/api/app/config.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing test**

Add:

```python
def test_live_macro_feed_health_uses_real_source_shape(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-economic-calendar/health")
    assert response.status_code == 200
    body = response.json()
    assert body["feed"]["id"] == "feed-economic-calendar"
    assert body["feed"]["vendor"] != "StreetLayer"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_macro_feed_health_uses_real_source_shape -v
```

Expected: FAIL because the macro connector is not implemented.

- [ ] **Step 3: Write minimal implementation**

Add a public macro/economic connector using a no-auth source that is reachable from Vercel:

- fetch release/event data
- derive:
  - freshness from newest release timestamp
  - continuity from event cadence
  - activity feature from release count / recent intensity
- emit feature lineage like:

```python
[
    "source:economic-calendar",
    "calendar:event-rate",
    "feat-economic-event-pressure",
]
```

Register the connector in the live registry.

- [ ] **Step 4: Run targeted test to verify it passes**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_macro_feed_health_uses_real_source_shape -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/live_connectors.py apps/api/app/services/live_vendor.py apps/api/app/config.py apps/api/tests/test_api.py
git commit -m "feat: add public macro live connector"
```

### Task 6: Filter live-mode API responses to live-backed records only

**Files:**
- Modify: `apps/api/app/services/current_state.py`
- Modify: `apps/api/app/repositories/feed_repository.py`
- Modify: `apps/api/app/repositories/feature_repository.py`
- Modify: `apps/api/app/repositories/incident_repository.py`
- Modify: `apps/api/app/repositories/metrics_repository.py`
- Test: `apps/api/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Add assertions for:

```python
def test_live_mode_overview_counts_only_live_feeds(live_client: TestClient):
    response = live_client.get("/api/v1/metrics/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"][0]["value"] == "3"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py::test_live_mode_overview_counts_only_live_feeds -v
```

Expected: FAIL because overview still uses synthetic fleet counts.

- [ ] **Step 3: Write minimal implementation**

Update `CurrentStateService` so that in live mode:

- feed lists are filtered to `LIVE_FEED_IDS`
- feature lists are filtered to `LIVE_FEATURE_IDS`
- incident lists are filtered by live-backed `feed_id`
- overview metrics derive `Tracked feeds`, `Active incidents`, and status buckets from those filtered live records only

Remove hardcoded `"18"` from the overview response in live mode.

- [ ] **Step 4: Run targeted and full API tests**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app/services/current_state.py apps/api/app/repositories/feed_repository.py apps/api/app/repositories/feature_repository.py apps/api/app/repositories/incident_repository.py apps/api/app/repositories/metrics_repository.py apps/api/tests/test_api.py
git commit -m "feat: filter live-mode API responses to real feeds only"
```

### Task 7: Update frontend labels and live-only dashboard semantics

**Files:**
- Modify: `apps/web/src/lib/api.ts`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/feeds/page.tsx`
- Modify: `apps/web/src/app/feeds/[feedId]/page.tsx`
- Modify: `apps/web/src/app/incidents/page.tsx`
- Modify: `apps/web/src/components/overview-live-panel.tsx`
- Modify: `apps/web/src/components/feed-live-panel.tsx`
- Modify: `apps/web/src/components/incidents-table.tsx`
- Test: `apps/web` build + typecheck

- [ ] **Step 1: Write the failing assertions by inspection**

Define the expected UI outcome before editing:

- dashboard tracked feed count shows `3`
- no `StreetLayer` or `EventPulse` appears in live mode
- no `Store Visit Intent Delta` or `Macro News Shock Sentiment` appears in live mode
- feed cards display real source names

- [ ] **Step 2: Run baseline verification**

Run:

```powershell
npm run build:web
npm run typecheck:web
```

Expected: PASS before changes, establishing a baseline.

- [ ] **Step 3: Write minimal implementation**

Update UI copy to reflect the real feed set:

- dashboard KPI copy should reflect actual live counts
- feed directory cards should show truthful source names
- incident/replay labels should use renamed feature names
- remove remaining hardcoded fake fleet semantics from live-facing surfaces

If layout/copy changes become awkward, use Google Stitch to improve those affected surfaces only.

- [ ] **Step 4: Run frontend verification**

Run:

```powershell
npm run build:web
npm run typecheck:web
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add apps/web/src/lib/api.ts apps/web/src/app/page.tsx apps/web/src/app/feeds/page.tsx apps/web/src/app/feeds/[feedId]/page.tsx apps/web/src/app/incidents/page.tsx apps/web/src/components/overview-live-panel.tsx apps/web/src/components/feed-live-panel.tsx apps/web/src/components/incidents-table.tsx
git commit -m "feat: update live UI to truthful source labels"
```

### Task 8: Update docs, deploy, and verify hosted live mode

**Files:**
- Modify: `README.md`
- Test: local API tests, web build, Vercel production checks

- [ ] **Step 1: Write the expected verification checklist**

Hosted live mode must verify:

- `/api/v1/feeds` returns only live-backed feed ids
- `/api/v1/incidents` has no seeded incident ids
- `/api/v1/metrics/overview` tracked feeds equals `3`
- `/feeds` shows only truthful live sources

- [ ] **Step 2: Update documentation**

Add docs covering:

- the three live public sources
- `DATA_MODE=live` behavior
- the fact that seeded mode and live mode now differ materially
- any selected public source URLs and runtime caveats

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m pytest apps/api/tests/test_api.py
npm run build:web
npm run typecheck:web
```

Expected: all PASS

- [ ] **Step 4: Deploy and smoke test**

Run:

```powershell
npx vercel --prod --yes --env DATA_MODE=live
```

Then verify:

```powershell
Invoke-WebRequest -UseBasicParsing https://hftminion.vercel.app/api/v1/feeds | Select-Object -ExpandProperty Content
Invoke-WebRequest -UseBasicParsing https://hftminion.vercel.app/api/v1/incidents | Select-Object -ExpandProperty Content
Invoke-WebRequest -UseBasicParsing https://hftminion.vercel.app/api/v1/metrics/overview | Select-Object -ExpandProperty Content
```

Expected:

- only three live feeds
- no `inc-1042` or `inc-1043`
- tracked feeds metric reflects `3`

- [ ] **Step 5: Commit**

```powershell
git add README.md
git commit -m "docs: describe live public vendor mode"
```

## Self-Review

- Spec coverage:
  - live-only filtering is covered in Tasks 1, 2, and 6
  - public news connector is covered in Task 4
  - public macro/economic connector is covered in Task 5
  - truthful UI labels and counts are covered in Task 7
  - deployment/doc updates are covered in Task 8
- Placeholder scan:
  - no `TODO` or `TBD` markers remain
  - each task includes files, commands, and expected outcomes
- Type consistency:
  - live feed ids are consistently `feed-binance-agg`, `feed-public-news`, `feed-economic-calendar`
  - live feature ids are consistently `feat-order-imbalance`, `feat-headline-velocity`, `feat-economic-event-pressure`

