# CS432 Assignment 3 - Module B Report

## Submission Details
- **GitHub Repository Link:** <ADD_REPO_LINK_HERE>
- **Video Demonstration Link:** <ADD_VIDEO_LINK_HERE>
- **Module:** Multi-User Behaviour and Stress Testing

---

## 1) Objective
This module evaluates whether the system remains correct and robust under multi-user load. The assignment requires:
- Concurrent usage testing
- Race-condition testing on critical operations
- Failure simulation and rollback safety
- Stress testing with high request volume
- ACID property verification (Atomicity, Consistency, Isolation, Durability)

This report summarizes the design, execution, and analysis of those experiments using:
- Locust scenarios in [Assignment-3/Module_B/locustfile.py](Assignment-3/Module_B/locustfile.py)
- Pipeline orchestration in [Assignment-3/Module_B/run_module_b_pipeline.sh](Assignment-3/Module_B/run_module_b_pipeline.sh)
- ACID invariant checks in [Assignment-3/Module_B/run_acid_checks.py](Assignment-3/Module_B/run_acid_checks.py)
- Artifact set [Assignment-3/Module_B/artifacts/20260405_064425](Assignment-3/Module_B/artifacts/20260405_064425)

---

## 2) Experimental Setup
- **API host:** http://127.0.0.1:8000
- **Load tool:** Locust (headless)
- **Database reset and seed:** [Assignment-2/Module_B/clean_database.sh](Assignment-2/Module_B/clean_database.sh)
- **OSRM service:** `docker start osrm-gujarat`

### Scenario Parameters
Defaults used by pipeline/Makefile:
- **Concurrent stage:** 120 users, spawn rate 20, duration 3 minutes
- **Race stage:** 120 users, spawn rate 30, duration 2 minutes

### Executed Output Folder
- [Assignment-3/Module_B/artifacts/20260405_064425](Assignment-3/Module_B/artifacts/20260405_064425)

---

## 3) Experiment Design

### 3.1 Concurrent Usage (Part 1)
Goal: many users perform normal operations simultaneously while preserving correctness.

Workload mix includes:
- Account bootstrap (register/login)
- Create rides
- Browse rides
- Book rides
- Host accept/reject pending bookings
- Start/end rides
- Admin monitoring endpoints

This stresses normal multi-user flow and checks that users do not corrupt each other’s state.

### 3.2 Race Condition Testing (Part 2)
Goal: many users attempt the **same critical operation** on shared data.

Design:
- One dedicated race host maintains a shared target ride.
- Many riders concurrently attempt booking this same ride.
- Host concurrently accepts/rejects pending bookings.
- Ride rollover creates a new race ride when old one is closed/full.

This intentionally induces contention around booking/accept transitions.

### 3.3 Failure Simulation
Failure-like conditions are induced via contention outcomes under race load:
- Booking/accept attempts on non-open ride
- High-collision timing between read-before-write and write operations

Expected behavior:
- Request-level rejection with controlled HTTP errors (e.g., 400)
- No partial or orphaned DB state after these failures

### 3.4 Stress Testing
Stress is applied by sustained high request volume in both stages:
- 11k+ requests in concurrent stage
- 3k+ requests in race stage

This validates both correctness and service responsiveness under heavy traffic.

### 3.5 How Concurrency and Race Are Implemented in `locustfile.py`

This section explains the exact mechanics used to generate concurrent behavior and race conditions.

#### Stage Wiring (Tag-Based Selection)
- Concurrent stage is executed with `--tags concurrent` in [run_module_b_pipeline.sh](run_module_b_pipeline.sh).
- Race stage is executed with `--tags race` in [run_module_b_pipeline.sh](run_module_b_pipeline.sh).
- This means the same `locustfile.py` drives both parts, but only the tagged tasks for that stage run.

#### Shared Coordination State
`SharedState` maintains global in-memory coordination among users:
- `race_ride_id`: the single hotspot ride for race testing
- `race_generation`: increments when a new race ride is created
- `account_seq`: deterministic account naming for host/rider bootstrap

At test start, `shared_state.reset()` clears old test state, ensuring stage-local Locust coordination begins fresh.

#### User Classes and Roles
- `HostConcurrentUser` (`weight = 4`): creates rides, manages pending bookings, starts/ends rides, browses.
- `RiderConcurrentUser` (`weight = 7`): browses open rides, books rides, checks own bookings.
- `AdminObserverUser` (`fixed_count = 1`): continuously observes admin endpoints.
- `RaceHostUser` (`fixed_count = 1`): controls race hotspot lifecycle and host-side accept/reject during race.

This creates role realism: many riders + fewer hosts + one observer + one race coordinator.

#### Concurrent Stage Mechanics (Broad Contention)
In concurrent mode, contention is distributed:
- Hosts mostly operate on rides they created (`self.owned_rides`).
- Riders pick from current open rides returned by `/rides`.
- Operations are mixed and weighted, not synchronized to one single ride.

Resulting behavior:
- High parallelism with lower hotspot pressure.
- Strong check of multi-user isolation and system throughput under realistic mixed usage.

#### Race Stage Mechanics (Hotspot Contention)
In race mode, contention is intentionally concentrated:
- `RaceHostUser.ensure_race_ride()` creates one shared race ride (`RACE_RIDE_CAPACITY` defaults to `2`).
- All race riders target this same `race_ride_id` in `race_book_shared_ride`.
- Each rider attempts once per generation using `last_race_generation_attempted`, then waits for rollover.
- `RaceHostUser.race_accept_or_reject` processes pending bookings while riders keep racing.
- `rollover_race_ride_if_closed` creates a new race ride when current one is not open or has zero seats.

This setup produces deterministic, repeated collisions on a critical operation (booking + acceptance flow).

#### Why Accept Can Fail Even With One Host
Although only one host accepts, the accept flow is still vulnerable to timing windows:
1. Host reads pending list (snapshot at time `t1`).
2. Between `t1` and accept POST at `t2`, ride state can change (e.g., become `Full` / not `Open`).
3. Backend validates current ride state at accept time and can return `400` (`Ride is not open for booking`).

So the race is not “host vs host”; it is **read-then-write timing against rapidly changing shared ride state** under high rider pressure.

#### Contention Classification Policy
`_handle_contention_response` categorizes outcomes:
- Success statuses: operation-specific success (e.g., 201 for booking, 200 for accept)
- Contention statuses: `{400, 404, 409}`
- Behavior controlled by `LOCUST_CONTENTION_MODE`:
  - `signal` (default): contention counts as failure in Locust report
  - `ignore`: contention is treated as expected and marked success

This allows the same workload to be used either for strict pass/fail metrics or contention observability.

#### Why Concurrent Stage Can Be Clean While Race Stage Shows Failures
- Concurrent: distributed targets, broader ride pool, less synchronized hotspot pressure.
- Race: single-ride hotspot + very low seat capacity + synchronized high-pressure booking attempts.

Therefore, zero concurrent failures and non-zero race contention failures are both expected and consistent with design.

---

## 4) Quantitative Results Analysis

### 4.1 Concurrent Stage Results
Source: [concurrent_stage_stats.csv](artifacts/20260405_064425/concurrent_stage_stats.csv), [concurrent_stage_failures.csv](artifacts/20260405_064425/concurrent_stage_failures.csv)

**Aggregated metrics:**
- Total requests: **11,226**
- Failures: **0**
- Failure rate: **0.00%**
- Average response time: **14.60 ms**
- Median (p50): **9 ms**
- p95: **29 ms**
- p99: **260 ms**
- Max: **470 ms**
- Throughput: **62.62 req/s**

**Interpretation:**
- Excellent stability under mixed concurrent operations.
- No endpoint-level failures recorded.
- Latency profile remains low for core read/write operations.

### 4.2 Race Stage Results
Source: [race_stage_stats.csv](artifacts/20260405_064425/race_stage_stats.csv), [race_stage_failures.csv](artifacts/20260405_064425/race_stage_failures.csv)

**Aggregated metrics:**
- Total requests: **3,398**
- Failures: **80**
- Failure rate: **2.35%**
- Average response time: **17.62 ms**
- Median (p50): **3 ms**
- p95: **43 ms**
- p99: **270 ms**
- Max: **460 ms**
- Throughput: **28.53 req/s**

**Failure breakdown (all contention-related):**
- `RACE POST /rides/bookings/{booking_id}/accept` -> 21 failures
  - Error: ride not open for booking
- `RACE POST /rides/{ride_id}/book` -> 59 failures
  - Error: ride not open for booking

**Interpretation:**
- Failures are expected under deliberate critical-section contention.
- No evidence of data corruption despite request-level conflicts.
- This stage validates rejection behavior under race pressure rather than zero-error throughput.

### 4.3 Exceptions
Source: [concurrent_stage_exceptions.csv](artifacts/20260405_064425/concurrent_stage_exceptions.csv), [race_stage_exceptions.csv](artifacts/20260405_064425/race_stage_exceptions.csv)

- Concurrent exceptions: **0**
- Race exceptions: **0**

Interpretation: application did not crash despite race contention.

---

## 5) ACID Testing (Individually)

ACID checks are executed by [run_acid_checks.py](Assignment-3/Module_B/run_acid_checks.py). Each stage snapshot validates a set of invariants.

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
Consistency means all business invariants remain valid after transactions.

Key consistency checks used:
- `seat_mismatch`
- `invalid_seat_bounds`
- `invalid_status_vs_seats`
- host booking/participant presence checks

Results:
- Stage B: [acid_stage_b.json](artifacts/20260405_064425/acid_stage_b.json) -> **no violations**
- Stage C: [acid_stage_c.json](artifacts/20260405_064425/acid_stage_c.json) -> **no violations**
- Stage D: [acid_stage_d.json](artifacts/20260405_064425/acid_stage_d.json) -> **no violations**

### 5.3 Isolation
Isolation means concurrent users should not corrupt each other’s writes.

Evidence from workload + checks:
- High-concurrency mixed operations in stage B with zero failures.
- Race collisions in stage C produce controlled request rejections rather than inconsistent DB state.
- No duplicate or contradictory rows after race stage.

Conclusion: isolation behavior is acceptable under both broad concurrency and targeted race pressure.

### 5.4 Durability
Durability means committed data persists across restart/failure scenarios.

Evidence:
- Post-pipeline durability snapshot [acid_stage_d.json](artifacts/20260405_064425/acid_stage_d.json) also reports zero violations.

Note:
- If no explicit backend restart command is provided, stage D still verifies post-run persistence checks; stronger durability proof includes an actual process restart between stage C and stage D.

---

## 6) Correctness, Failure Handling, and Multi-User Safety

### 6.1 Correctness of Operations
- Core flows (create/book/accept/start/end) execute correctly under load.
- DB invariants remain valid after each stage.

### 6.2 Failure Handling
- Race contention failures are safely rejected (HTTP 400) without crashing app.
- No partial/invalid persistence observed in ACID snapshots.

### 6.3 Multi-User Conflict Handling
- Concurrent stage demonstrates safe parallelism across users.
- Race stage demonstrates safe rejection under critical-section contention.

---

## 7) Observations and Limitations

### Observations
- System performs strongly under concurrent mixed traffic with zero failures.
- Under deliberate race pressure, controlled contention failures appear as expected.
- Despite contention, all measured consistency invariants remain intact.

### Limitations
- Race stage prioritizes contention realism over zero request failure rate.
- Durability evidence is strongest when explicit backend/database restart is performed before stage D check.
- Reported metrics reflect one representative run; repeated runs are recommended for confidence intervals.

---

## 8) Conclusion
The system demonstrates robust multi-user behavior:
- Strong concurrent stability and low latency
- Safe handling of race conflicts without state corruption
- Clean ACID invariant snapshots across concurrent, race, and durability stages

Overall, the implementation meets the assignment goal of building a reliable, conflict-safe, and load-resilient system.
