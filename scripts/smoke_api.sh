#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8099}"
DATABASE_URL="${DATABASE_URL:-sqlite:///./.smoke_hexarch.db}"
HEXARCH_API_TOKEN="${HEXARCH_API_TOKEN:-dev-token}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-15}"

export DATABASE_URL
export HEXARCH_API_TOKEN

echo "Starting API on http://${HOST}:${PORT} ..."
python -m uvicorn hexarch_cli.server.app:app --host "$HOST" --port "$PORT" --log-level warning &
PID=$!

cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

end=$((SECONDS + TIMEOUT_SECONDS))
while [ $SECONDS -lt $end ]; do
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
      echo "OK: /health responded"
      exit 0
    fi
  else
    if python - <<'PY' >/dev/null 2>&1
import urllib.request
urllib.request.urlopen("http://${HOST}:${PORT}/health", timeout=2).read()
PY
    then
      echo "OK: /health responded"
      exit 0
    fi
  fi
  sleep 0.25
done

echo "Health check failed: API did not respond within ${TIMEOUT_SECONDS}s" >&2
exit 1
