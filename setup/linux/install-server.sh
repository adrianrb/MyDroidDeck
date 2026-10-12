#!/usr/bin/env bash
# Install the MyDroidDeck server on Linux/macOS — the non-Windows "fork".
#
# Creates a virtualenv, installs the server package, writes a launcher and a
# systemd --user unit, seeds data/runtime.json (no login, port 56997) and opens
# the settings page.
#
# Usage: setup/linux/install-server.sh [--prefix DIR] [--port N] [--no-service]
set -euo pipefail

PREFIX="${XDG_DATA_HOME:-$HOME/.local/share}/mydroiddeck"
PORT=56997
SERVICE=1

while [ $# -gt 0 ]; do
    case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --no-service) SERVICE=0; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 2 ;;
    esac
done

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SETUP_DIR/.." && pwd)"
DATA="$PREFIX/data"
VENV="$PREFIX/venv"
BIN="$PREFIX/bin"

command -v python3 >/dev/null 2>&1 || { echo "python3 não encontrado" >&2; exit 1; }

mkdir -p "$PREFIX" "$DATA" "$BIN"

if [ ! -x "$VENV/bin/python" ]; then
    echo "Criando virtualenv em $VENV …"
    python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install --upgrade pip >/dev/null
"$VENV/bin/pip" install -e "$ROOT/server"

# Launcher: reads data/runtime.json (host/port) and starts the ASGI app.
cat > "$BIN/mydroiddeck" <<EOF
#!/usr/bin/env bash
export MYDROIDDECK_DATABASE_URL="sqlite:///$DATA/mydroiddeck.db"
export MYDROIDDECK_RUNTIME_CONFIG_FILE="$DATA/runtime.json"
export MYDROIDDECK_ICON_CACHE_DIR="$DATA/icons"
export MYDROIDDECK_ADMIN_AUTH_ENABLED="\${MYDROIDDECK_ADMIN_AUTH_ENABLED:-false}"
cd "$ROOT/server"
exec "$VENV/bin/python" "$ROOT/server/launch.py"
EOF
chmod +x "$BIN/mydroiddeck"

# Seed the runtime config on the first install (keep an existing one).
if [ ! -f "$DATA/runtime.json" ]; then
    cat > "$DATA/runtime.json" <<EOF
{
  "visible_on_network": false,
  "port": $PORT,
  "start_on_logon": false
}
EOF
fi

if [ "$SERVICE" = 1 ] && command -v systemctl >/dev/null 2>&1; then
    UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p "$UNIT_DIR"
    cat > "$UNIT_DIR/mydroiddeck.service" <<EOF
[Unit]
Description=MyDroidDeck server

[Service]
ExecStart=$BIN/mydroiddeck
Restart=on-failure

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload || true
    systemctl --user enable --now mydroiddeck.service 2>/dev/null || true
    echo "Serviço systemd (usuário): mydroiddeck.service"
fi

echo "Launcher: $BIN/mydroiddeck"
echo "Config  : http://127.0.0.1:$PORT/admin/config"

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://127.0.0.1:$PORT/admin/config" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:$PORT/admin/config" >/dev/null 2>&1 || true
fi
