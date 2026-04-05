# Experiment Summary (20260405_155611)

- Artifact folder: `artifacts/20260405_155611`

## Concurrent Stage
- Total requests: 10,340
- Failures: 0 (0.00%)
- Avg response time: 32.79 ms
- p50/p95/p99: 13.00 / 120.00 / 410.00 ms
- Max response time: 1427.22 ms
- Throughput: 57.94 req/s
- Exceptions: 0
- Top failures: none

## Race Stage
- Total requests: 3,131
- Failures: 84 (2.68%)
- Avg response time: 34.46 ms
- p50/p95/p99: 4.00 / 300.00 / 670.00 ms
- Max response time: 1307.84 ms
- Throughput: 26.28 req/s
- Exceptions: 0
- Top failures:
  - POST RACE POST /rides/{ride_id}/book -> 84 | CatchResponseError('race-contention race-book status=400 details: Ride is not open for booking')

## ACID Stage B (Post-Concurrent)
- Snapshot stage: stage_b_concurrent
- Timestamp (UTC): 2026-04-05T10:29:21.168655+00:00
- Result: no violations
- Violating checks: none

## ACID Stage C (Post-Race)
- Snapshot stage: stage_c_race
- Timestamp (UTC): 2026-04-05T10:31:22.086199+00:00
- Result: no violations
- Violating checks: none

## ACID Stage D (Durability/Post-Restart)
- Snapshot stage: stage_d_post_restart
- Timestamp (UTC): 2026-04-05T10:31:27.598963+00:00
- Result: no violations
- Violating checks: none
