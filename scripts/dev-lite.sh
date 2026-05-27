#!/usr/bin/env bash
# Lightweight local run: no Python reload watcher, smaller searches, webpack dev (less RAM than Turbopack on some Macs).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

export JOB_COPILOT_LIGHT=1

if command -v conda &>/dev/null; then
  eval "$(conda shell.bash hook)" 2>/dev/null || true
  conda activate job-copilot 2>/dev/null || true
fi

echo "Lite mode: JOB_COPILOT_LIGHT=1 (fewer SerpAPI calls, no careers scrape, 3 people/role)"
echo "Starting agents on http://127.0.0.1:8000 (no --reload) ..."
cd "$ROOT/agents"
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
AGENTS_PID=$!

cleanup() {
  echo ""
  echo "Stopping agents (pid $AGENTS_PID)..."
  kill "$AGENTS_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 1
if ! curl -sf --max-time 3 "http://127.0.0.1:8000/health" >/dev/null; then
  echo "Warning: agents health check failed — check conda env job-copilot and apps/web/.env"
fi

echo "Starting web on http://localhost:3000 (webpack dev) ..."
cd "$ROOT/apps/web"
npm run dev -- --webpack
