# Load-Test Stability Changes (April 5, 2026)

This document records code changes made to reduce `500` failures caused by SQLAlchemy pool exhaustion under Locust load.

## 1) Made DB pool settings configurable

**File:** `core/config.py`

### Changes
- Added:
  - `DB_POOL_SIZE` (default `30`)
  - `DB_MAX_OVERFLOW` (default `60`)
  - `DB_POOL_TIMEOUT` (default `15` seconds)

### Why this helps
- Earlier pool settings were fixed and small (`10 + 20 overflow`, `5s timeout`), which caused fast queue exhaustion.
- Configurable values let you tune pool capacity for local testing vs production without code edits.
- Increasing timeout modestly reduces spurious failures during short bursts.

---

## 2) Reduced per-request DB work in session bootstrap

**File:** `db/session.py`

### Changes
- `create_engine(...)` now uses config-driven pool values instead of hard-coded constants.
- Removed extra fallback query in `get_db_session()` that fetched `AuthCredential` on every authenticated request when username/role were missing.

### Why this helps
- That extra lookup consumed a DB connection and query before normal route logic, increasing contention significantly at high concurrency.
- Removing it reduces connection checkout pressure and DB round trips for all authenticated endpoints (`/rides`, `/rides/my/bookings`, etc.).

---

## 3) Propagated actor metadata from JWT claims

**Files:** `core/security.py`, `main.py`, `api/routes/auth.py`

### Changes
- `create_access_token(...)` now optionally embeds:
  - `usr` (username)
  - `role`
- Added `decode_access_token_payload(...)` helper.
- HTTP middleware now reads `sub`, `usr`, `role` from token payload and sets request context directly.
- Register/login token issuance now includes username and role claims.

### Why this helps
- Preserves actor context (`username`, `role`) for request metadata without querying DB in session setup.
- Keeps behavior/functionality while lowering DB work per request.

---

## 4) Expected impact on your observed failures

### Before
- Repeated pool timeouts (`QueuePool limit ... timeout 5.00`) produced cascaded `500`s for read-heavy endpoints.

### After
- Fewer DB queries per authenticated request.
- Better pool headroom and tunability.
- Lower probability of synchronized pool starvation during spikes.

---

## 5) Suggested runtime values for your next test

Start with:
- `DB_POOL_SIZE=40`
- `DB_MAX_OVERFLOW=80`
- `DB_POOL_TIMEOUT=20`

Then run a step-up load test (e.g., 100 -> 200 -> 300 users) and compare:
- `500` error counts
- p95/p99 latency for `GET /rides` and `GET /rides/my/bookings`
- timeout stack traces in backend logs

---

## 6) Remaining known bottleneck

- ORS is still not configured (`routing.ors_failed ... ORS_API_KEY is not configured`), so expensive fallback logic remains on booking acceptance paths.
- Setting `ORS_API_KEY` (or simplifying that path for benchmark mode) should further reduce tail latency and pool contention.
