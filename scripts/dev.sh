#!/usr/bin/env bash
# One command: Python agents (8000) + Next.js (3000)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if command -v conda &>/dev/null; then
  eval "$(conda shell.bash hook)" 2>/dev/null || true
  conda activate job-copilot 2>/dev/null || true
fi

echo "Starting agents on http://127.0.0.1:8000 ..."
cd "$ROOT/agents"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
AGENTS_PID=$!

cleanup() {
  echo ""
  echo "Stopping agents (pid $AGENTS_PID)..."
  kill "$AGENTS_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2
if ! curl -sf "http://127.0.0.1:8000/health" >/dev/null; then
  echo "Warning: agents health check failed — check conda env and apps/web/.env"
fi

echo "Starting web on http://localhost:3000 ..."
cd "$ROOT/apps/web"
npm run dev
