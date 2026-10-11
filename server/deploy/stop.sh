#!/usr/bin/env bash
# Stop the MyDroidDeck server started by deploy/start.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE="$ROOT/deploy/server.pid"

if [ -f "$PIDFILE" ]; then
    pid="$(cat "$PIDFILE")"
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "MyDroidDeck parado (pid $pid)."
    else
        echo "O processo registrado (pid $pid) não está mais ativo."
    fi
    rm -f "$PIDFILE"
else
    echo "Nenhum pid registrado. Se ainda houver um servidor órfão:" >&2
    echo "  pkill -f 'uvicorn app.main:app'" >&2
fi