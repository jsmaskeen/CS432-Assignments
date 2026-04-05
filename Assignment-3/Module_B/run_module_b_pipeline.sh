#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
LOCUST_BIN="${LOCUST_BIN:-locust}"
HOST="${HOST:-http://127.0.0.1:8000}"
MAX_USERS=200
BACKEND_ENV="${BACKEND_ENV:-${PROJECT_ROOT}/Assignment-2/Module_B/backend/.env}"
RESET_DB="${RESET_DB:-1}"
RESET_DB_CMD="${RESET_DB_CMD:-${PROJECT_ROOT}/Assignment-2/Module_B/clean_database.sh}"

if [[ -z "${PYTHON_BIN:-}" || "${PYTHON_BIN}" == "python" ]]; then
  if [[ -x "${PROJECT_ROOT}/backend/.venv/bin/python" ]]; then
    PYTHON_BIN="${PROJECT_ROOT}/backend/.venv/bin/python"
  fi
fi

if [[ -z "${LOCUST_BIN:-}" || "${LOCUST_BIN}" == "locust" ]]; then
  if [[ -x "${PROJECT_ROOT}/backend/.venv/bin/locust" ]]; then
    LOCUST_BIN="${PROJECT_ROOT}/backend/.venv/bin/locust"
  fi
fi

CONCURRENT_USERS="${CONCURRENT_USERS:-120}"
CONCURRENT_SPAWN="${CONCURRENT_SPAWN:-20}"
CONCURRENT_TIME="${CONCURRENT_TIME:-3m}"

RACE_USERS="${RACE_USERS:-120}"
RACE_SPAWN="${RACE_SPAWN:-30}"
RACE_TIME="${RACE_TIME:-2m}"

FAILURE_USERS="${FAILURE_USERS:-120}"
FAILURE_SPAWN="${FAILURE_SPAWN:-30}"
FAILURE_TIME="${FAILURE_TIME:-2m}"

STRESS_USERS="${STRESS_USERS:-200}"
STRESS_SPAWN="${STRESS_SPAWN:-40}"
STRESS_TIME="${STRESS_TIME:-5m}"

WITH_FAILURE="${WITH_FAILURE:-0}"
WITH_STRESS="${WITH_STRESS:-0}"

WITH_DURABILITY="${WITH_DURABILITY:-0}"
RESTART_BACKEND_CMD="${RESTART_BACKEND_CMD:-}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${SCRIPT_DIR}/artifacts/${TIMESTAMP}"
mkdir -p "${OUT_DIR}"

validate_users() {
  local users="$1"
  local label="$2"
  if ! [[ "$users" =~ ^[0-9]+$ ]]; then
    echo "ERROR: ${label} must be an integer, got '${users}'"
    exit 2
  fi
  if (( users < 1 )); then
    echo "ERROR: ${label} must be >= 1"
    exit 2
  fi
  if (( users > MAX_USERS )); then
    echo "ERROR: ${label}=${users} exceeds cap ${MAX_USERS}."
    echo "This implementation supports up to ${MAX_USERS} concurrent users for makefile/pipeline commands."
    exit 2
  fi
}

validate_users "$CONCURRENT_USERS" "CONCURRENT_USERS"
validate_users "$RACE_USERS" "RACE_USERS"
validate_users "$FAILURE_USERS" "FAILURE_USERS"
validate_users "$STRESS_USERS" "STRESS_USERS"

if [[ "${RESET_DB}" == "1" ]]; then
  echo "[0] Resetting database with clean_database.sh"
  if [[ ! -x "${RESET_DB_CMD}" ]]; then
    echo "ERROR: RESET_DB_CMD not executable: ${RESET_DB_CMD}"
    exit 2
  fi
  "${RESET_DB_CMD}"
  echo "Database reset complete."
  sleep 5
else
  echo "[0] Skipping database reset (RESET_DB=${RESET_DB})"
fi

run_acid_stage() {
  local stage_name="$1"
  local output_path="$2"

  set +e
  "${PYTHON_BIN}" "${SCRIPT_DIR}/run_acid_checks.py" \
    --stage "${stage_name}" \
    --env-file "${BACKEND_ENV}" \
    --output "${output_path}"
  local rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    echo "ACID stage '${stage_name}': no violations"
  elif [[ $rc -eq 1 ]]; then
    echo "ACID stage '${stage_name}': violations found (captured in ${output_path})"
  else
    echo "ACID stage '${stage_name}': failed with exit code ${rc}"
    exit $rc
  fi
}

run_locust_stage() {
  local stage_label="$1"
  local allow_failures="$2"
  shift
  shift

  set +e
  "${LOCUST_BIN}" "$@"
  local rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    echo "Locust stage '${stage_label}': completed with no Locust failures"
  elif [[ $rc -eq 1 ]]; then
    if [[ "${allow_failures}" == "1" ]]; then
      echo "Locust stage '${stage_label}': request failures detected (continuing; see CSV artifacts)"
    else
      echo "Locust stage '${stage_label}': request failures detected (failing pipeline)"
      exit 1
    fi
  else
    echo "Locust stage '${stage_label}': failed with exit code ${rc}"
    exit $rc
  fi
}

echo "[1] Running concurrent stage (users=${CONCURRENT_USERS}, spawn=${CONCURRENT_SPAWN}, time=${CONCURRENT_TIME})"
run_locust_stage "concurrent" "0" -f "${SCRIPT_DIR}/locustfile.py" \
  --host "${HOST}" \
  --tags concurrent \
  -u "${CONCURRENT_USERS}" -r "${CONCURRENT_SPAWN}" -t "${CONCURRENT_TIME}" \
  --headless \
  --csv "${OUT_DIR}/concurrent_stage"

echo "[2] Capturing ACID snapshot after concurrent stage"
run_acid_stage "stage_b_concurrent" "${OUT_DIR}/acid_stage_b.json"

echo "[3] Running race stage (users=${RACE_USERS}, spawn=${RACE_SPAWN}, time=${RACE_TIME})"
run_locust_stage "race" "1" -f "${SCRIPT_DIR}/locustfile.py" \
  --host "${HOST}" \
  --tags race \
  -u "${RACE_USERS}" -r "${RACE_SPAWN}" -t "${RACE_TIME}" \
  --headless \
  --csv "${OUT_DIR}/race_stage"

echo "[4] Capturing ACID snapshot after race stage"
run_acid_stage "stage_c_race" "${OUT_DIR}/acid_stage_c.json"

if [[ "${WITH_FAILURE}" == "1" ]]; then
  echo "[5] Running failure simulation stage (users=${FAILURE_USERS}, spawn=${FAILURE_SPAWN}, time=${FAILURE_TIME})"
  run_locust_stage "failure" "1" -f "${SCRIPT_DIR}/locustfile.py" \
    --host "${HOST}" \
    --tags failure \
    -u "${FAILURE_USERS}" -r "${FAILURE_SPAWN}" -t "${FAILURE_TIME}" \
    --headless \
    --csv "${OUT_DIR}/failure_stage"

  echo "[6] Capturing ACID snapshot after failure stage"
  run_acid_stage "stage_f_failure" "${OUT_DIR}/acid_stage_f.json"
else
  echo "[5] Skipping failure stage (set WITH_FAILURE=1 to enable)"
fi

if [[ "${WITH_STRESS}" == "1" ]]; then
  echo "[7] Running stress stage (users=${STRESS_USERS}, spawn=${STRESS_SPAWN}, time=${STRESS_TIME})"
  run_locust_stage "stress" "1" -f "${SCRIPT_DIR}/locustfile.py" \
    --host "${HOST}" \
    --tags stress \
    -u "${STRESS_USERS}" -r "${STRESS_SPAWN}" -t "${STRESS_TIME}" \
    --headless \
    --csv "${OUT_DIR}/stress_stage"

  echo "[8] Capturing ACID snapshot after stress stage"
  run_acid_stage "stage_s_stress" "${OUT_DIR}/acid_stage_s.json"
else
  echo "[7] Skipping stress stage (set WITH_STRESS=1 to enable)"
fi

if [[ "${WITH_DURABILITY}" == "1" ]]; then
  echo "[9] Durability stage requested"
  if [[ -n "${RESTART_BACKEND_CMD}" ]]; then
    echo "Executing backend restart command..."
    eval "${RESTART_BACKEND_CMD}"
  else
    echo "WARNING: WITH_DURABILITY=1 but RESTART_BACKEND_CMD is not set."
    echo "Running stage_d snapshot without restart."
  fi

  run_acid_stage "stage_d_post_restart" "${OUT_DIR}/acid_stage_d.json"
else
  echo "[9] Skipping durability stage (set WITH_DURABILITY=1 to enable)"
fi

echo "Pipeline complete. Artifacts: ${OUT_DIR}"
