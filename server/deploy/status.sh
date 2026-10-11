#!/usr/bin/env bash
# Show whether the MyDroidDeck server is up and healthy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE="$ROOT/deploy/server.pid"
PORT="${MYDROIDDECK_PORT:-8000}"

# Read .env to learn whether the listener is HTTP or HTTPS.
if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT/.env"
    set +a
fi
SCHEME="http"
CURL_OPTS=(-fsS)
if [ -n "${MYDROIDDECK_SSL_CERTFILE:-}" ] && [ -n "${MYDROIDDECK_SSL_KEYFILE:-}" ]; then
    SCHEME="https"
    CURL_OPTS+=(-k) # self-signed dev certificate
fi

pid=""
if [ -f "$PIDFILE" ]; then
    pid="$(cat "$PIDFILE")"
fi

if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "processo: ativo (pid $pid)"
else
    echo "processo: parado"
fi

if curl "${CURL_OPTS[@]}" --max-time 3 "$SCHEME://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo "serviço : respondendo em $SCHEME://127.0.0.1:$PORT"
else
    echo "serviço : sem resposta em $SCHEME://127.0.0.1:$PORT"
fi