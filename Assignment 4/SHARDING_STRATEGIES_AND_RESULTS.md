# Sharding Strategy and Results

This document summarizes the final strategy comparison and measured outcomes for Assignment 4 sharding.

## 1) Strategy Families Implemented

### A) Hash-based routing
- Strategy: deterministic modulo routing
- Mapping: `shard_id = (RideID - 1) % 3`
- Runtime behavior: no metadata lookup required

### B) Directory exact routing
- Strategy: per-ride lookup from `Ride_Shard_Directory`
- Runtime behavior: metadata lookup + fallback logic

### C) Directory range routing
- Strategy: key-range lookup from `Ride_Shard_Range_Directory`
- Runtime behavior: rule evaluation + fallback logic

Final runtime default is hash-based modulo. Directory exact/range are retained for migration control and rebalancing support.

## 2) Data and Environment Snapshot

- Shard count: 3
- Final evaluated dataset:
  - rides: 6000
  - bookings: 13370
- Entropy analysis source: live DB, shard-scope aggregation (`--source db --db-scope auto`)

## 3) Commands Used (Latest Run)

From `Assignment 4/backend`:

```bash
../..//.venv/Scripts/python.exe -c "from db.session import SessionLocal; from sqlalchemy import text; db=SessionLocal(); db.execute(text('DELETE FROM Ride_Shard_Range_Directory')); db.commit(); db.close(); print('Range rules cleared')"
../..//.venv/Scripts/python.exe -m scripts.compare_shard_lookup_strategies --iterations 20000 --output shard_lookup_comparison_baseline.json
../..//.venv/Scripts/python.exe -m scripts.configure_ride_shard_ranges --replace --rule 1-2000:0 --rule 2001-4000:1 --rule 4001-*:2
../..//.venv/Scripts/python.exe -m scripts.compare_shard_lookup_strategies --iterations 20000 --output shard_lookup_comparison_with_ranges.json
../..//.venv/Scripts/python.exe -m scripts.shard_key --source db --db-scope auto --entropy-output shard_key_entropy_comparison.json
../..//.venv/Scripts/python.exe -m scripts.plot_shard_key_distribution --input shard_key_entropy_comparison.json --output ../../images/shard_key_policy_distribution.png
```

Artifacts:
- `Assignment 4/backend/scripts/shard_lookup_comparison_baseline.json`
- `Assignment 4/backend/scripts/shard_lookup_comparison_with_ranges.json`
- `Assignment 4/backend/scripts/shard_key_entropy_comparison.json`
- `Assignment 4/images/shard_key_policy_distribution.png`

## 4) Lookup Strategy Benchmarks

### Baseline (no range rules)

| Strategy | Avg (ms) | P95 (ms) | P99 (ms) | Max (ms) | Lookups/s | Normalized Entropy | Imbalance Spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| `modulo` | 0.000234 | 0.000300 | 0.000500 | 0.031800 | 1,979,041.95 | 0.999938 | 190 |
| `directory_exact_cache` | 0.000520 | 0.000900 | 0.001200 | 0.061200 | 1,154,054.77 | 0.999885 | 257 |

### Range-enabled (3 rules active)

Rules:
- `1-2000 -> shard 0`
- `2001-4000 -> shard 1`
- `4001-* -> shard 2`

| Strategy | Avg (ms) | P95 (ms) | P99 (ms) | Max (ms) | Lookups/s | Normalized Entropy | Imbalance Spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| `modulo` | 0.000223 | 0.000300 | 0.000500 | 0.048900 | 2,079,391.15 | 0.999938 | 190 |
| `directory_exact_cache` | 0.000402 | 0.000600 | 0.000900 | 0.032000 | 1,453,794.77 | 0.999885 | 257 |
| `directory_range_cache` | 0.000438 | 0.000500 | 0.000700 | 0.028800 | 1,462,800.97 | 0.999960 | 138 |

## 5) Entropy-Based Shard-Key Comparison

Entropy definition used:

$$
H = -\sum_{i=0}^{2} p_i \log_2(p_i),\quad
H_{max} = \log_2(3) \approx 1.5849625,\quad
H_{normalized} = \frac{H}{H_{max}}
$$

Where $p_i$ is the fraction of rides assigned to shard $i$.

### Candidate key ranking (latest)

| Candidate | Method | Counts (0/1/2) | Normalized Entropy | Imbalance Spread |
|---|---|---:|---:|---:|
| `ride_id_mod3` | `(RideID - 1) % 3` | 2000 / 2000 / 2000 | 1.000000 | 0 |
| `route_pair_hash` | `md5(Start_GeoHash|End_GeoHash) % 3` | 2016 / 2003 / 1981 | 0.999976 | 35 |
| `end_geohash_hash` | `md5(End_GeoHash) % 3` | 2038 / 1974 / 1988 | 0.999914 | 64 |
| `start_geohash_hash` | `md5(Start_GeoHash) % 3` | 1949 / 2024 / 2027 | 0.999851 | 78 |
| `host_plus_start_hash` | `md5(Host_MemberID|Start_GeoHash) % 3` | 2031 / 1941 / 2028 | 0.999801 | 90 |
| `host_member_id_mod3` | `(Host_MemberID - 1) % 3` | 2018 / 2063 / 1919 | 0.999587 | 144 |
| `vehicle_type_hash` | `md5(Vehicle_Type) % 3` | 1478 / 1486 / 3036 | 0.942542 | 1558 |
| `ride_status_hash` | `md5(Ride_Status) % 3` | 6000 / 0 / 0 | 0.000000 | 6000 |

Distribution figure:

![Shard distribution across candidate shard-key policies](images/shard_key_policy_distribution.png)

## 6) Final Choice and Rationale

### Chosen runtime shard key
- `RideID` with deterministic modulo: `(RideID - 1) % 3`

### Why this was selected
- Highest throughput among tested lookup strategies.
- Perfect shard-key balance on final dataset (entropy 1.0, spread 0).
- Strong query alignment: `ride_id` is the dominant route and join handle in ride-centric endpoints.
- Stable key after insertion, minimizing re-sharding churn.
- Simpler and lower-overhead runtime path than metadata-dependent routing.

### Why directory strategies are still kept
- Exact directory is useful for migration overrides and controlled placement.
- Range directory is useful for planned rebalancing experiments.
- Both are operational tools, not default runtime routing.

## 7) Notes

- The `shard_key` script now supports live DB analysis with shard-aware scope selection.
- Recommended invocation for production-like evaluation:
  - `--source db --db-scope auto`
- This prevents false conclusions when `MYSQL_PORT` points to one shard instance.
