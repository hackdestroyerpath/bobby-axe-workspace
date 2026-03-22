#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/openclaw/.openclaw/workspace-jack"
URL="${SNAPSHOT_LOOKUP_URL:-http://127.0.0.1:8787}"
DEMO_SNAPSHOT="${SNAPSHOT_LOOKUP_DEMO_SNAPSHOT:-snapshot_20260321T235503Z_c0a7cb5a}"

cd "$ROOT"

echo "[smoke] checking health: $URL/health"
curl -fsS "$URL/health"

echo

echo "[smoke] checking lookup: $URL/lookup?snapshot_id=$DEMO_SNAPSHOT"
RESP=$(curl -fsS "$URL/lookup?snapshot_id=$DEMO_SNAPSHOT")
python3 - <<'PY' "$RESP"
import json, sys
payload = json.loads(sys.argv[1])
print(json.dumps({
    'lookup': payload.get('lookup'),
    'snapshot': payload.get('snapshot'),
    'readiness': payload.get('readiness'),
    'downstream': payload.get('downstream'),
}, ensure_ascii=False, indent=2))
if not payload.get('lookup', {}).get('found'):
    raise SystemExit('lookup did not resolve a snapshot')
PY

echo

echo "[smoke] ok"
