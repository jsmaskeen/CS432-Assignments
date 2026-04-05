# Assignment 3 - Module B: Load Testing (Part 1 & Part 2)

This guide explains how to run:
- **Part 1:** Concurrent Usage testing
- **Part 2:** Race Condition testing

---

## Prerequisites

From repository root:

1. **Backend dependencies/environment** should be set up (`backend/.venv` exists).
2. **Backend API** should be running at `http://127.0.0.1:8000`.
3. **Database credentials** should be set in:
   - `Assignment-2/Module_B/backend/.env`
4. (Recommended) Start OSRM container if route/distance APIs are required by backend:

```bash
docker start osrm-gujarat
```

---

## Quick Start (Recommended)

Run from:

```bash
cd Assignment-3/Module_B
```

### Part 1: Concurrent Usage

```bash
make concurrent
```

Then run ACID snapshot for this stage:

```bash
make acid-b
```

### Part 2: Race Condition

```bash
make race
```

Then run ACID snapshot for this stage:

```bash
make acid-c
```

---

## Full Pipeline (Both Stages + ACID)

```bash
make pipeline
```

Artifacts are generated under:

- `Assignment-3/Module_B/artifacts/<timestamp>/`

Typical files:
- `concurrent_stage_*.csv`
- `race_stage_*.csv`
- `acid_stage_b.json`
- `acid_stage_c.json`

---

## Durability Stage (Optional)

Run full pipeline + post-restart ACID snapshot:

```bash
make pipeline-durability
```

If needed, provide restart command via environment:

```bash
RESTART_BACKEND_CMD="<your restart command>" make pipeline-durability
```

---

## Useful Overrides

You can override users/spawn/time per stage:

```bash
CONCURRENT_USERS=150 CONCURRENT_SPAWN=25 CONCURRENT_TIME=4m make concurrent
RACE_USERS=150 RACE_SPAWN=40 RACE_TIME=3m make race
```

Cap is enforced at `200` users by Makefile/pipeline.

---

## Direct Locust Commands (without make)

From `Assignment-3/Module_B`:

### Concurrent

```bash
../../backend/.venv/bin/locust -f locustfile.py --host http://127.0.0.1:8000 --tags concurrent -u 120 -r 20 -t 3m --headless --csv concurrent_stage
```

### Race

```bash
../../backend/.venv/bin/locust -f locustfile.py --host http://127.0.0.1:8000 --tags race -u 120 -r 30 -t 2m --headless --csv race_stage
```

---

## Troubleshooting

- If you see stale-state issues (e.g., duplicate booking conflicts across reruns), reset DB first:

```bash
Assignment-2/Module_B/clean_database.sh
```

- If backend schema errors appear after DB reset, restart backend once.
- If race-stage contention failures are expected for your experiment, check `LOCUST_CONTENTION_MODE` behavior in `locustfile.py`.
