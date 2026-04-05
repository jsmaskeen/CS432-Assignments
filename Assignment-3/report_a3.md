# CS432 Assignment 3 - Overall Report

## Submission Details
- **Group Name:** RAJAK (Ride Along--Just Act Kool)
- **Students:**
  - Aarsh Wankar
  - Abhinav Khot
  - Jaskirat Singh Maskeen
  - Karan Sagar Gandhi
  - Romit Mohane
- **GitHub Repository Link:** <ADD_REPO_LINK_HERE>
- **Video Demonstration Link:** <ADD_VIDEO_LINK_HERE>

---

## 1) Objective and Scope

Assignment 3 evaluates the backend along two complementary dimensions:

1. **Module A (Transactional Correctness):** proves ACID properties through focused tests that target commit/rollback semantics, invariant preservation, visibility isolation, and persistence behavior under interruption.
2. **Module B (Operational Robustness):** validates behavior under multi-user traffic, explicit contention, and sustained load, while continuously checking post-stage ACID invariants.

The combined scope is intended to answer two questions:

- *Is the transactional engine logically correct for key data operations?* (Module A)
- *Does the system remain safe and predictable when many users act concurrently in realistic and adversarial patterns?* (Module B)

---

## 2) System Context and Validation Strategy

### 2.1 Core Entities in Validation
All validation tracks repeatedly exercise core relational objects:

- `Members`
- `Rides`
- `Bookings`

These are central to user identity, ride lifecycle, and participation state transitions.

### 2.2 Why Two Modules Were Necessary
Module A and Module B serve different purposes and together provide stronger confidence than either alone:

- **Module A** isolates transactional behavior in controlled conditions.
- **Module B** verifies emergent behavior under concurrency and load where timing races naturally appear.

This layered approach helps distinguish between:

- deterministic transactional bugs,
- expected contention outcomes,
- and performance-related degradation under stress.

---

## 3) Module A - ACID Validation (Detailed)

### 3.1 Test Coverage Layout
Primary tests are organized by property:

- Atomicity: `tests/test_atomicity_context_manager.py`
- Consistency: `tests/test_consistency.py`
- Isolation: `tests/test_isolation_acid.py`
- Durability: `tests/test_durability_acid.py`

All property groups include operations that span multiple relations, not single-row toy cases, to reflect practical transaction paths.

### 3.2 Atomicity Findings
Atomicity checks confirm that transactions behave as indivisible units:

- successful paths commit fully,
- failure paths rollback fully,
- interruptions during an in-flight transaction do not leave partial persistent state,
- pre-commit crash-style exits do not materialize committed effects.

**Assessment:** atomic commit/rollback boundary handling is correct for covered scenarios.

### 3.3 Consistency Findings
Consistency checks validate both syntactic and semantic constraints:

- valid relational chains are accepted,
- invalid values are rejected by CHECK/NOT NULL constraints,
- invalid references are rejected by FK constraints,
- cross-field ride invariants remain enforced.

**Assessment:** schema-level invariants hold reliably under tested operations.

### 3.4 Isolation Findings
Isolation checks validate visibility and transaction scoping:

- uncommitted writes remain private to transaction-aware reads,
- external readers observe committed state,
- thread-level transaction boundaries are respected,
- re-entrant same-thread transaction misuse is rejected.

**Assessment:** isolation semantics are consistent with intended transaction visibility rules.

### 3.5 Durability Findings
Durability tests verify post-commit persistence and WAL semantics:

- committed operations survive subsequent access,
- WAL records capture commit history,
- pre-commit interruption does not imply persistence,
- post-commit interruption preserves committed effects.

**Assessment:** durability behavior aligns with expected commit-persistence guarantees in tested paths.

### 3.6 Module A Conclusion
Module A establishes strong evidence that ACID properties are not only declared but behaviorally enforced in representative transactional flows.

---

## 4) Module B - Concurrency and Load Validation (Detailed)

### 4.1 Environment and Inputs
- API host: `http://127.0.0.1:8000`
- Load tool: Locust (headless)
- DB reset before run: [Assignment-2/Module_B/clean_database.sh](Assignment-2/Module_B/clean_database.sh)
- Stage orchestrator: [Assignment-3/Module_B/run_module_b_pipeline.sh](Module_B/run_module_b_pipeline.sh)
- Latest analyzed run: [Assignment-3/Module_B/artifacts/20260405_155611](Module_B/artifacts/20260405_155611)

Default parameters:

- Concurrent: 120 users, spawn 20, duration 3m
- Race: 120 users, spawn 30, duration 2m

### 4.2 Stage Design and Intent

#### Concurrent Stage (`--tags concurrent`)
Intent: broad multi-user realism with distributed contention.

Workload includes:

- host ride creation,
- ride browsing,
- rider booking attempts,
- booking acceptance/rejection,
- ride start/end,
- admin observation endpoints.

This stage tests whether normal parallel behavior remains stable and logically isolated.

#### Race Stage (`--tags race`)
Intent: concentrated hotspot contention.

Mechanics:

- one shared ride is maintained by race host,
- many riders target the same ride,
- host processes pending booking decisions,
- ride rollover creates repeated contention windows.

Host pre-check behavior:

- race host checks ride state before accept/reject,
- avoids stale host-side accept attempts on non-open rides,
- leaves rider-side hotspot contention as primary race signal.

### 4.3 Quantitative Results (Latest Run)

#### 4.3.1 Concurrent Metrics
- Total requests: **10,340**
- Failures: **0** (**0.00%**)
- Average response time: **32.79 ms**
- p50: **13 ms**
- p95: **120 ms**
- p99: **410 ms**
- Max: **1427 ms**
- Throughput: **57.94 req/s**

Interpretation:

- endpoint-level reliability is strong under mixed workload,
- tail latency grows under load but not with correctness regressions,
- no request failures in concurrent stage suggest stable path behavior under distributed contention.

#### 4.3.2 Race Metrics
- Total requests: **3,131**
- Failures: **84** (**2.68%**)
- Average response time: **34.46 ms**
- p50: **4 ms**
- p95: **300 ms**
- p99: **670 ms**
- Max: **1308 ms**
- Throughput: **26.28 req/s**

Failure class observed:

- `RACE POST /rides/{ride_id}/book` -> 84
- HTTP 400: `Ride is not open for booking`

Interpretation:

- failures are contention-consistent and expected for a hotspot race scenario,
- these are controlled rejections, not crashes,
- exception logs remain empty for both stages.

### 4.4 ACID Snapshots in Operational Pipeline
Post-stage checks via `run_acid_checks.py`:

- Stage B (`acid_stage_b.json`): **no violations**
- Stage C (`acid_stage_c.json`): **no violations**
- Stage D (`acid_stage_d.json`): **no violations**

Implication:

- request-level contention does not propagate into persistent invariant corruption.

### 4.5 Durability Flow in Pipeline
`pipeline-durability` executes:

1. concurrent stage,
2. stage-B ACID snapshot,
3. race stage,
4. stage-C ACID snapshot,
5. restart step (through `RESTART_BACKEND_CMD`, when configured),
6. stage-D (`stage_d_post_restart`) ACID snapshot.

Purpose of `RESTART_BACKEND_CMD`:

- inject explicit restart boundary,
- convert stage D from simple post-run validation into stronger post-restart durability evidence.

---

## 5) Unified ACID Assessment (Module A + Module B)

### 5.1 Atomicity
- Module A proves transaction-level all-or-nothing semantics directly.
- Module B shows no invariant drift after heavy multi-user execution.

**Combined view:** atomicity is both theoretically validated and operationally corroborated.

### 5.2 Consistency
- Module A validates schema and relational constraints.
- Module B confirms no consistency violations across stage snapshots.

**Combined view:** consistency constraints remain intact in both isolated and loaded environments.

### 5.3 Isolation
- Module A validates uncommitted visibility boundaries and transaction scoping.
- Module B race stage demonstrates conflict containment through controlled rejection.

**Combined view:** isolation boundaries are respected and race conflicts are safely surfaced.

### 5.4 Durability
- Module A validates persistence semantics and WAL behavior under interruption.
- Module B validates post-run/post-restart snapshot integrity.

**Combined view:** durability guarantees are supported at both transaction mechanism and operational pipeline levels.

---

## 6) Risk Areas, Limitations, and Practical Notes

### 6.1 What This Report Does Not Claim
- It does not claim zero-latency degradation under all loads.
- It does not claim infinite scalability from a single-run profile.
- It does not treat expected race rejections as correctness failures.

### 6.2 Current Limitations
- Metrics represent specific runs, not full confidence intervals.
- Tail latency increases significantly under heavier pressure.
- Race-stage contention profile is intentionally adversarial and not equivalent to normal production traffic.

### 6.3 Recommended Next Steps
1. Run repeated pipelines (N>=5) and publish mean/stddev for key percentiles.
2. Add saturation diagnostics (DB connection pool, lock wait, queue depth) to correlate with latency tails.
3. Extend durability proof by enforcing and logging verified restart command execution in every durability run.
4. Add endpoint-level SLO thresholds for p95/p99 and fail pipeline on regression.

---

## 7) Final Conclusion

Assignment 3 demonstrates that RAJAK is transaction-safe and multi-user robust:

- **Module A** provides strong direct evidence that ACID behavior is correctly implemented at transactional boundaries.
- **Module B** demonstrates stable concurrent operation, expected and controlled race contention handling, and preserved invariants after load stages.
- **Combined evidence** indicates that the system maintains logical correctness even when operational pressure increases.

Overall, the Assignment-3 implementation satisfies its objectives with reproducible, multi-layer validation of correctness, contention safety, and durability-oriented behavior.
