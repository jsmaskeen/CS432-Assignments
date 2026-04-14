#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

if ! command -v python >/dev/null 2>&1; then
  echo "Error: python is not available in PATH."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is not available in PATH."
  exit 1
fi

echo "[1/5] Preparing backend virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  python -m venv "$VENV_DIR"
fi

if [ -x "$VENV_DIR/Scripts/python.exe" ]; then
  PY_EXE="$VENV_DIR/Scripts/python.exe"
elif [ -x "$VENV_DIR/bin/python" ]; then
  PY_EXE="$VENV_DIR/bin/python"
else
  echo "Error: Could not find Python executable in virtual environment."
  exit 1
fi

echo "[2/5] Installing backend dependencies..."
"$PY_EXE" -m pip install --upgrade pip
"$PY_EXE" -m pip install -r "$BACKEND_DIR/requirements.txt"

echo "[3/5] Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install

echo "[4/5] Starting backend..."
cd "$BACKEND_DIR"
"$PY_EXE" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[5/5] Starting frontend..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Stopping dev servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo ""
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:5173"
echo "Press Ctrl+C to stop both servers."

wait "$BACKEND_PID" "$FRONTEND_PID"
