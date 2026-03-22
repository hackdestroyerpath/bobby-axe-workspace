#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/openclaw/.openclaw/workspace-jack"
VENV="$ROOT/collector/.venv/bin/activate"
HOST="${SNAPSHOT_LOOKUP_HOST:-127.0.0.1}"
PORT="${SNAPSHOT_LOOKUP_PORT:-8787}"

cd "$ROOT"
source "$VENV"

echo "[snapshot-lookup-ui] starting on http://$HOST:$PORT"
exec python tools/snapshot_lookup_server.py --host "$HOST" --port "$PORT"
