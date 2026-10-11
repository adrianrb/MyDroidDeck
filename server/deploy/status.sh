#!/usr/bin/env bash
# Show whether the MyDroidDeck server is up and healthy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE="$ROOT/deploy/server.pid"
PORT="${MYDROIDDECK_PORT:-8000}"

pid=""
if [ -f "$PIDFILE" ]; then
    pid="$(cat "$PIDFILE")"
fi

if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "processo: ativo (pid $pid)"
else
    echo "processo: parado"
fi

if curl -fsS --max-time 3 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo "http    : respondendo em 127.0.0.1:$PORT"
else
    echo "http    : sem resposta"
fi