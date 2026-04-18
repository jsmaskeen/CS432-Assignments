# Sharding Strategy and Results (Default Strategy: Modulo)

This document explains the sharding setup currently in use for Assignment 4.

Decision for now: default to deterministic modulo (`ride_id_mod_3`), while keeping exact-directory and range-directory modes available for testing and benchmarking.

## 1) Active Lookup Strategy

### Deterministic modulo (`ride_id_mod_3`)
- Definition: compute shard directly from `RideID`.
- Formula: `shard_id = (ride_id - 1) % 3`.
- Implementation source: `Assignment 4/backend/db/sharding.py` (`shard_id_for_ride_id`).
- Why this is chosen now:
  - Very low lookup overhead (pure arithmetic).
  - No metadata dependency needed for shard selection.
  - Simple and predictable behavior during development.

### Exact-directory lookup (`directory_exact`)
- Definition: resolve `RideID` through `Ride_Shard_Directory` when the mode is enabled.
- Useful for tests that want to validate explicit per-ride placement or migration overrides.

### Range-directory lookup (`directory_range`)
- Definition: resolve `RideID` through `Ride_Shard_Range_Directory` when the mode is enabled.
- Useful for testing rebalancing by key ranges.

## 2) Table Sharding Layout

### Ride-centric tables (sharded across shard_0, shard_1, shard_2)
- `Rides`
- `Bookings`
- `Ride_Chat`
- `Ride_Participants`
- `Reputation_Reviews`
- `Cost_Settlements`

These are distributed by ride shard placement.

### Centralized tables (primary DB)
- `Ride_Shard_Directory`
- `Ride_Shard_Range_Directory`
- `Review_Shard_Directory`
- Other global entities (locations, preferences, etc.)

Even though directory tables exist, the default operational policy is modulo lookup. The other two modes remain available by changing `RIDE_SHARD_LOOKUP_MODE`.

## 3) What the Microbenchmark Measures

The benchmark script `Assignment 4/backend/scripts/compare_shard_lookup_strategies.py` measures only shard-id lookup cost in Python for sampled ride IDs.

What it does:
- Loads existing ride IDs from `Ride_Shard_Directory`.
- Randomly samples `iterations` ride IDs.
- For each strategy under test, computes shard ID and records timing.
- Reports:
  - `avg_ms`
  - `p95_ms`
  - `p99_ms`
  - `max_ms`
  - `lookups_per_second`
  - sampled shard distribution

What it does not do:
- It does not measure full API latency.
- It does not include network, serialization, DB query execution, or transaction overhead.
- It should be treated as routing-logic overhead only.

## 4) Commands Run (Relative to Root)

Root directory for these commands: `CS432-Assignments`

### A) Functional tests
```bash
cd "Assignment 4/backend"
../../venv/bin/python -m pytest tests/core/test_sharding_directory_strategy.py tests/api/routes/test_rides_sharding.py -q
```

Observed result:
- `9 passed`

### B) Benchmark run (baseline modulo-focused run)
```bash
cd "Assignment 4/backend"
set -a && source .env >/dev/null 2>&1 && set +a
../../venv/bin/python -m scripts.compare_shard_lookup_strategies --iterations 15000 --output shard_lookup_comparison_before_ranges.json
```

### C) Benchmark run (comparison with configured range rules, for evaluation only)
```bash
cd "Assignment 4/backend"
set -a && source .env >/dev/null 2>&1 && set +a
../../venv/bin/python -m scripts.configure_ride_shard_ranges --replace --rule 1-48:0 --rule 49-96:1 --rule 97-145:2
../../venv/bin/python -m scripts.compare_shard_lookup_strategies --iterations 15000 --output shard_lookup_comparison_after_ranges.json
```

Result artifacts:
- `Assignment 4/backend/scripts/shard_lookup_comparison_before_ranges.json`
- `Assignment 4/backend/scripts/shard_lookup_comparison_after_ranges.json`

## 5) Results (Formatted)

Dataset size: `145` rides, iterations: `15000`

### A) Baseline run (no range rules)

| Strategy | Avg (ms) | P95 (ms) | P99 (ms) | Max (ms) | Lookups/s |
|---|---:|---:|---:|---:|---:|
| `modulo` | 0.0001637 | 0.0002410 | 0.0002810 | 0.0197980 | 3,016,826 |
| `directory_exact_cache` | 0.0001789 | 0.0002000 | 0.0002900 | 0.0065330 | 3,249,915 |

### B) Range-evaluation run (3 configured range rules)

Rules used during evaluation:
- `1-48 -> shard 0`
- `49-96 -> shard 1`
- `97-145 -> shard 2`

| Strategy | Avg (ms) | P95 (ms) | P99 (ms) | Max (ms) | Lookups/s |
|---|---:|---:|---:|---:|---:|
| `modulo` | 0.0001242 | 0.0001810 | 0.0002110 | 0.0082150 | 3,941,409 |
| `directory_exact_cache` | 0.0001723 | 0.0002310 | 0.0002900 | 0.0090570 | 3,418,314 |
| `directory_range_cache` | 0.0002174 | 0.0002910 | 0.0004110 | 0.0073940 | 3,002,577 |

## 6) Interpretation

- Modulo is consistently the lowest-overhead strategy in this microbenchmark.
- Directory exact lookup is close, but still adds a metadata-map access layer.
- Range-directory lookup has the highest overhead in this benchmark due to rule evaluation.
- Since current goal is simple and fast routing, modulo is the default strategy for runtime.
- The other modes stay in the codebase for controlled testing, migration, and comparison.

## 7) Current Policy (for this phase)

- Use modulo lookup as the default operational strategy.
- Keep exact-directory and range-directory machinery available behind `RIDE_SHARD_LOOKUP_MODE`.
- If/when rebalancing becomes a requirement, switch the mode and re-run the same benchmark + API-level latency tests.
