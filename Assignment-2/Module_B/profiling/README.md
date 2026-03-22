# Profiling Reproduction Guide

This guide explains how to reproduce the latency experiments used in the report.

## 1) Prerequisites

- MySQL is running and has the `cabSharing` database loaded.
- `backend/.env` is configured (at least `MYSQL_USER`, `MYSQL_PASSWORD`, and DB host settings).
- Python dependencies are installed in backend and profiling environments.
- Backend API is running at `http://127.0.0.1:8000`.

Start backend (from workspace root):

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

Use a second terminal for profiling commands.

## 2) One-pass before/after experiment

This runs baseline profiling, applies indexes, reruns profiling, and writes comparison markdown:

```bash
cd profiling
bash profile.sh
```

Outputs generated:

- `profiling_results_before.json`
- `profiling_results_after.json`
- `profiling_results_before.md`
- `profiling_results_after.md`
- `profiling_comparison.md`

## 3) Repeated experiment (recommended for report)

Run repeated before/after measurements (default 5 runs each):

```bash
cd .
python3 profiling/run_repeated_benchmarks.py --runs 5
```

Outputs generated:

- Raw run files in `profiling/repeated_runs/raw/`
- Aggregated JSON: `profiling/repeated_comparison.json`
- Aggregated markdown: `profiling/repeated_comparison.md`

## 4) Regenerate charts/tables for notebook

```bash
cd .
python3 profiling/plot_optimized_endpoints.py
```

Then re-run cells in `report.ipynb` to refresh report visuals.

## 5) Capture EXPLAIN evidence

Use the report notebook EXPLAIN cell or run manually with MySQL client. Capture both before-index and after-index plans for the same SQL queries.

## 6) Optional rollback of indexes

```bash
cd .
set -a && source backend/.env && set +a
export MYSQL_PWD="$MYSQL_PASSWORD"
mysql -u"$MYSQL_USER" cabSharing < profiling/indexes_drop.sql
```

## 7) Reproducibility notes

- Keep dataset size constant (`seed_db_massive.py`) for all runs.
- Avoid running other heavy workloads during benchmarking.
- Compare the same endpoint set before and after indexing.
- Interpret results per endpoint: some broad APIs remain slow due to large response payload size, even when indexes are present.
