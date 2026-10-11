#!/usr/bin/env bash
# Start the MyDroidDeck server detached from this terminal.
#
# The process leaves the terminal session (setsid + nohup), so pressing Ctrl+C
# here will not stop it. Logs: deploy/server.log · PID: deploy/server.pid
#
# Usage: deploy/start.sh   (env: MYDROIDDECK_HOST / MYDROIDDECK_PORT)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST="${MYDROIDDECK_HOST:-0.0.0.0}"
PORT="${MYDROIDDECK_PORT:-8000}"
LOG="$ROOT/deploy/server.log"
PIDFILE="$ROOT/deploy/server.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "MyDroidDeck já está em execução (pid $(cat "$PIDFILE"))." >&2
    echo "Reinicie com: deploy/stop.sh && deploy/start.sh" >&2
    exit 0
fi

# Load .env (pairing code, database URL) into the server's environment.
if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT/.env"
    set +a
fi

mkdir -p "$ROOT/deploy" "$ROOT/data"

# Serve HTTPS when a certificate is configured (see deploy/gen-cert.sh).
TLS_ARGS=()
SCHEME="http"
if [ -n "${MYDROIDDECK_SSL_CERTFILE:-}" ] && [ -n "${MYDROIDDECK_SSL_KEYFILE:-}" ]; then
    TLS_ARGS=(--ssl-keyfile "$MYDROIDDECK_SSL_KEYFILE" --ssl-certfile "$MYDROIDDECK_SSL_CERTFILE")
    SCHEME="https"
fi

setsid nohup .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT" \
    ${TLS_ARGS[@]+"${TLS_ARGS[@]}"} \
    >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDFILE"

echo "MyDroidDeck no ar: $SCHEME://$HOST:$PORT"
echo "  log : $LOG"
echo "  pid : $(cat "$PIDFILE")"
echo "  parar: deploy/stop.sh"