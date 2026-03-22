#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

set -a
source backend/.env
set +a
export MYSQL_PWD="${MYSQL_PASSWORD}"

./clean_database.sh
cd backend && python3 seed_db_massive.py
cd ../profiling && python3 profile_apis.py
cp profiling_results.json profiling_results_before.json
cp profiling_results.md profiling_results_before.md

cd "$ROOT_DIR"
./clean_database.sh
cd backend && python3 seed_db_massive.py
cd "$ROOT_DIR"
mysql -u"${MYSQL_USER}" cabSharing < profiling/indexes_apply.sql

cd profiling
python3 profile_apis.py
cp profiling_results.json profiling_results_after.json
cp profiling_results.md profiling_results_after.md

python3 compare_profiling_results.py \
  --before profiling_results_before.json \
  --after profiling_results_after.json \
  --out profiling_comparison.md
