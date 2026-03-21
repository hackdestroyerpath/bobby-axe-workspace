#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/tmp/runtime_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/bobby_live_loop.log"
STATUS_FILE="$LOG_DIR/bobby_live_loop.status"

PYTHON_BIN="${PYTHON_BIN:-python3}"
INTERVAL_SEC="${BOBBY_INTERVAL_SEC:-60}"
CANDLES_LIMIT="${BOBBY_CANDLES_LIMIT:-50}"
TIMEOUT_SEC="${BOBBY_TIMEOUT_SEC:-10}"
ITERATIONS="${BOBBY_ITERATIONS:-0}"
CONFIG_PATH="${BOBBY_CONFIG_PATH:-$ROOT_DIR/config.json}"
START_TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"

cat > "$STATUS_FILE" <<EOF
status=starting
started_at=$START_TS
pid=$$
config=$CONFIG_PATH
interval_sec=$INTERVAL_SEC
candles_limit=$CANDLES_LIMIT
timeout_sec=$TIMEOUT_SEC
iterations=$ITERATIONS
log_file=$LOG_FILE
EOF

cleanup() {
  local exit_code=$?
  cat > "$STATUS_FILE" <<EOF
status=stopped
started_at=$START_TS
stopped_at=$(date '+%Y-%m-%d %H:%M:%S %Z')
pid=$$
exit_code=$exit_code
config=$CONFIG_PATH
interval_sec=$INTERVAL_SEC
candles_limit=$CANDLES_LIMIT
timeout_sec=$TIMEOUT_SEC
iterations=$ITERATIONS
log_file=$LOG_FILE
EOF
}
trap cleanup EXIT

{
  echo "[$START_TS] starting Bobby live paper loop"
  echo "config=$CONFIG_PATH interval_sec=$INTERVAL_SEC candles_limit=$CANDLES_LIMIT timeout_sec=$TIMEOUT_SEC iterations=$ITERATIONS"
  sed 's/^/status_file_init: /' "$STATUS_FILE"

  cat > "$STATUS_FILE" <<EOF
status=running
started_at=$START_TS
last_launch_at=$(date '+%Y-%m-%d %H:%M:%S %Z')
pid=$$
config=$CONFIG_PATH
interval_sec=$INTERVAL_SEC
candles_limit=$CANDLES_LIMIT
timeout_sec=$TIMEOUT_SEC
iterations=$ITERATIONS
log_file=$LOG_FILE
EOF

  "$PYTHON_BIN" "$ROOT_DIR/paper_loop.py" \
    --config "$CONFIG_PATH" \
    --live \
    --interval-sec "$INTERVAL_SEC" \
    --iterations "$ITERATIONS" \
    --candles-limit "$CANDLES_LIMIT" \
    --timeout-sec "$TIMEOUT_SEC"
} >> "$LOG_FILE" 2>&1
