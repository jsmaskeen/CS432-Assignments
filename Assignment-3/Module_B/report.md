# CS432 Assignment 3 - Module B Report

## Submission Details

- **GitHub Repository Link:** <ADD_REPO_LINK_HERE>
- **Video Demonstration Link:** <ADD_VIDEO_LINK_HERE>
- **Module:** Multi-User Behaviour and Stress Testing

---

## 1) Scope and Objective

Module B validates backend correctness under concurrent access, contention, induced failures, and high load. Verification is based on request-level metrics and post-stage ACID invariant checks.

Primary requirements covered:

1. Concurrent usage under mixed operations
2. Race-condition behavior on booking/accept critical path
3. Failure simulation with rollback validation
4. Stress behavior under sustained load
5. ACID property verification (A/C/I/D)

---

## 2) Test Harness and Methodology

### 2.1 Tooling

1. Load generation: [Assignment-3/Module_B/locustfile.py](Assignment-3/Module_B/locustfile.py)
2. Stage orchestration: [Assignment-3/Module_B/run_module_b_pipeline.sh](Assignment-3/Module_B/run_module_b_pipeline.sh), [Assignment-3/Module_B/Makefile](Assignment-3/Module_B/Makefile)
3. Invariant verification: [Assignment-3/Module_B/run_acid_checks.py](Assignment-3/Module_B/run_acid_checks.py), [Assignment-3/Module_B/acid_invariant_queries.sql](Assignment-3/Module_B/acid_invariant_queries.sql)

### 2.2 Execution Environment

1. API host: `http://127.0.0.1:8000`
2. DB reset before runs: [Assignment-2/Module_B/clean_database.sh](Assignment-2/Module_B/clean_database.sh)
3. Artifacts directory: [Assignment-3/Module_B/artifacts/20260405_064425](Assignment-3/Module_B/artifacts/20260405_064425)

### 2.3 Workload Stages

1. Concurrent (`--tags concurrent`): mixed host/rider/admin workflows.
2. Race (`--tags race`): hotspot contention on shared ride booking/acceptance.
3. Failure (`--tags failure`): deterministic fault injection during critical transactions.
4. Stress (`--tags stress`): high sustained mixed traffic.

---

## 3) Backend and Test Infrastructure Changes

The following changes were made to implement Failure + Stress stages.

### 3.1 Failure Injection (Backend)

1. Added deterministic chaos state manager:
   [Assignment-2/Module_B/backend/core/chaos.py](Assignment-2/Module_B/backend/core/chaos.py)
2. Added admin-only chaos control endpoints:
   [Assignment-2/Module_B/backend/api/routes/testing.py](Assignment-2/Module_B/backend/api/routes/testing.py)

- `GET /api/v1/testing/chaos`
- `POST /api/v1/testing/chaos/enable`
- `POST /api/v1/testing/chaos/reset`

3. Added transaction hook in booking acceptance path:
   [Assignment-2/Module_B/backend/api/routes/bookings.py](Assignment-2/Module_B/backend/api/routes/bookings.py)

- Hook: `bookings.accept.post_flush`
- Behavior: raise simulated runtime failure before commit, rollback existing transaction.

4. Added transaction hook in ride completion path:
   [Assignment-2/Module_B/backend/api/routes/rides.py](Assignment-2/Module_B/backend/api/routes/rides.py)

- Hook: `rides.end.before_settlement_insert`
- Behavior: abort before settlement insert, rollback transaction.

### 3.2 Load Harness and Pipeline Changes

1. Added Locust failure coordinator and stage tags:
   [Assignment-3/Module_B/locustfile.py](Assignment-3/Module_B/locustfile.py)
2. Added Make targets:
   [Assignment-3/Module_B/Makefile](Assignment-3/Module_B/Makefile)

- `make failure`, `make stress`, `make acid-f`, `make acid-s`, `make pipeline-extended`

3. Added pipeline stage wiring for failure/stress snapshots:
   [Assignment-3/Module_B/run_module_b_pipeline.sh](Assignment-3/Module_B/run_module_b_pipeline.sh)
4. Added stage usage docs:
   [Assignment-3/Module_B/README.md](Assignment-3/Module_B/README.md)

---

## 4) Results Summary

### 4.1 Concurrent Stage

Source: [Assignment-3/Module_B/artifacts/20260405_064425/concurrent_stage_stats.csv](Assignment-3/Module_B/artifacts/20260405_064425/concurrent_stage_stats.csv)

1. Requests: 11,226
2. Failures: 0 (0.00%)
3. p50: 9 ms, p95: 29 ms, p99: 260 ms
4. Throughput: 62.62 req/s

Result: stable under mixed concurrent operations.

### 4.2 Race Stage

Source: [Assignment-3/Module_B/artifacts/20260405_064425/race_stage_stats.csv](Assignment-3/Module_B/artifacts/20260405_064425/race_stage_stats.csv), [Assignment-3/Module_B/artifacts/20260405_064425/race_stage_failures.csv](Assignment-3/Module_B/artifacts/20260405_064425/race_stage_failures.csv)

1. Requests: 3,398
2. Failures: 80 (2.35%)
3. p50: 3 ms, p95: 43 ms, p99: 270 ms
4. Throughput: 28.53 req/s

Failure class: expected contention rejections on race booking/accept paths.

### 4.3 Failure Simulation Stage

Source: [Assignment-3/Module_B/artifacts/20260405_064425/failure_stage_stats.csv](Assignment-3/Module_B/artifacts/20260405_064425/failure_stage_stats.csv), [Assignment-3/Module_B/artifacts/20260405_064425/failure_stage_failures.csv](Assignment-3/Module_B/artifacts/20260405_064425/failure_stage_failures.csv), [Assignment-3/Module_B/artifacts/20260405_064425/acid_stage_f.json](Assignment-3/Module_B/artifacts/20260405_064425/acid_stage_f.json)

1. Requests: 2,580
2. Failures: 26 (about 1.01%)
3. p50: 5 ms, p95: 260 ms, p99: 15,000 ms
4. Throughput: 21.50 req/s
5. Failure type observed: `RACE POST /rides/bookings/{booking_id}/accept` returned 502 (26 occurrences)

ACID outcome:

1. `has_violations = false`
2. All invariant checks returned 0 violations.

Result: injected failures were contained and rolled back without partial data persistence.

### 4.4 Stress Stage

Source: [Assignment-3/Module_B/artifacts/20260405_064425/stress_requests.csv](Assignment-3/Module_B/artifacts/20260405_064425/stress_requests.csv), [Assignment-3/Module_B/artifacts/20260405_064425/stress_failures.csv](Assignment-3/Module_B/artifacts/20260405_064425/stress_failures.csv), [Assignment-3/Module_B/artifacts/20260405_064425/acid_stage_s.json](Assignment-3/Module_B/artifacts/20260405_064425/acid_stage_s.json)

1. Requests: 4,076
2. Failures: 170 (about 4.17%)
3. p50: 73 ms, p95: 45,000 ms, p99: 71,000 ms
4. Throughput: 15.94 req/s

Observed failure classes:

1. Expected contention: `POST /rides/{ride_id}/book` with 409 (duplicate booking attempts).
2. Load-related server errors: 500s on ride list/detail/my-bookings and ride creation/stats endpoints.

No new duplicate/settlement corruption was observed in test-generated data.

Result: stress revealed performance saturation and server-error behavior, while structural data integrity remained controllable in test-generated workload scope.

---

## 5) ACID Assessment by Property

### 5.1 Atomicity

Atomicity means operations either fully apply or fully rollback (no partial writes).

Validated using invariants such as:

- No orphan/invalid settlements
- No missing participant for confirmed booking
- No duplicate critical rows (bookings/participants/settlements)
- Additional atomicity-specific checks added in checker:
    - `participant_without_confirmed_booking`
    - `non_confirmed_booking_with_participant`

Result summary (from stage snapshots): no atomicity-related invariant violations detected.

### 5.2 Consistency

1. Concurrent/race/failure stages maintained invariant consistency.
2. Stress stage exposed consistency issues in baseline seeded segment and service saturation indicators.

Conclusion: consistency is strong in validated dynamic paths; baseline data quality and overload handling require separate hardening.

### 5.3 Isolation

1. Race contention produced controlled request failures instead of cross-user corruption.
2. No duplicate booking/participant/settlement anomalies in failure stage.

Conclusion: isolation behavior is acceptable for tested concurrency paths.

### 5.4 Durability

Durability is validated through stage D snapshot flow when pipeline-durability is executed with restart procedure. Existing stage artifacts support persistence verification after run completion.

---

## 6) Technical Conclusion

The system demonstrates robust transactional behavior under concurrent use, hotspot contention, and deterministic failure injection. Failure simulation confirms rollback safety and absence of partial writes in validated flows. Stress testing exposes practical capacity limits (tail-latency escalation and 500 errors), identifying the next optimization targets as connection/resource tuning and overload-path hardening.

Overall, Module B requirements were implemented end-to-end with reproducible load stages, explicit fault injection, and invariant-based correctness checks.
