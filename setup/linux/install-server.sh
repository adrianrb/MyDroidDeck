#!/usr/bin/env bash
# MyDroidDeck server installer for Linux and WSL — the "Linux/WSL" fork.
#
# Per-user and self-contained: installs under $HOME/MyDroidDeck by default (no root
# needed), creates a virtualenv, seeds data/runtime.json (no login, port 56997) and,
# optionally, autostarts the server at logon and adds a desktop shortcut. On WSL it
# opens the Configuration page in the Windows browser.
#
# Usage: setup/linux/install-server.sh [options]
#   --prefix DIR        install location (default: $HOME/MyDroidDeck)
#   --port N            TCP port (default: 56997)
#   --autostart MODE    auto|systemd|xdg|profile|none (default: auto)
#   --no-desktop        skip the desktop / Start-menu shortcut
#   --no-open           do not open the browser
#   --no-start          do not start the server now
#   --install-deps      install missing prerequisites with sudo (asks first)
#   --yes               non-interactive: keep every default
#   --uninstall         remove the autostart entry and shortcuts, then exit
#   --dry-run           print what would be done; change nothing
#   -h, --help          this help
set -euo pipefail

APP_NAME="MyDroidDeck"
DEFAULT_PORT=56997
DEFAULT_PREFIX="$HOME/MyDroidDeck"

PREFIX=""
PORT="$DEFAULT_PORT"
AUTOSTART="auto"
DESKTOP=1
OPEN_BROWSER=1
START_NOW=1
INSTALL_DEPS=0
ASSUME_YES=0
UNINSTALL=0
DRY_RUN=0

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
log() { printf '==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf 'aviso: %s\n' "$*" >&2; }
die() {
    printf 'erro: %s\n' "$*" >&2
    exit 1
}
have() { command -v "$1" >/dev/null 2>&1; }

run() {
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] %s\n' "$*"
        return 0
    fi
    "$@"
}

# write_file PATH  — file contents on stdin
write_file() {
    local path="$1"
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] escrever %s\n' "$path"
        cat >/dev/null
        return 0
    fi
    mkdir -p "$(dirname "$path")"
    cat >"$path"
}

# Copy the deployable server tree (like setup/build-offline.sh does for Windows):
# just the code, never the developer's .venv/data/deploy leftovers.
copy_server() { # DST
    local dst="$1"
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] copiar o servidor para %s\n' "$dst"
        return 0
    fi
    rm -rf "$dst"
    mkdir -p "$dst"
    cp -r "$ROOT/server/app" "$dst/app"
    cp "$ROOT/server/version.txt" "$dst/version.txt"
    cp "$ROOT/server/actions.example.json" "$dst/actions.example.json"
    cp "$ROOT/server/launch.py" "$dst/launch.py"
    cp "$ROOT/server/pyproject.toml" "$dst/pyproject.toml"
    if [ -f "$ROOT/server/README.md" ]; then
        cp "$ROOT/server/README.md" "$dst/README.md"
    fi
    find "$dst" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
}

# yes/no prompt; default y or n. Non-interactive keeps the default.
prompt_yes_no() {
    local question="$1" default="${2:-y}" answer
    if [ "$ASSUME_YES" = 1 ]; then
        [ "$default" = "y" ]
        return
    fi
    if [ ! -t 0 ]; then
        [ "$default" = "y" ]
        return
    fi
    if [ "$default" = "y" ]; then
        question="$question [S/n] "
    else
        question="$question [s/N] "
    fi
    read -r -p "$question" answer || answer=""
    answer="${answer,,}"
    if [ -z "$answer" ]; then
        [ "$default" = "y" ]
    elif [[ "$answer" == s* || "$answer" == y* ]]; then
        return 0
    else
        return 1
    fi
}

# --------------------------------------------------------------------------- #
# argument parsing
# --------------------------------------------------------------------------- #
while [ $# -gt 0 ]; do
    case "$1" in
    --prefix)
        [ $# -ge 2 ] || die "--prefix exige um valor"
        PREFIX="$2"
        shift 2
        ;;
    --prefix=*) PREFIX="${1#*=}"; shift ;;
    --port)
        [ $# -ge 2 ] || die "--port exige um valor"
        PORT="$2"
        shift 2
        ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --autostart)
        [ $# -ge 2 ] || die "--autostart exige um valor"
        AUTOSTART="$2"
        shift 2
        ;;
    --autostart=*) AUTOSTART="${1#*=}"; shift ;;
    --no-desktop) DESKTOP=0; shift ;;
    --no-open) OPEN_BROWSER=0; shift ;;
    --no-start) START_NOW=0; shift ;;
    --install-deps) INSTALL_DEPS=1; shift ;;
    --yes | -y) ASSUME_YES=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h | --help)
        sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *) die "opção desconhecida: $1" ;;
    esac
done

case "$AUTOSTART" in
auto | systemd | xdg | profile | none) ;;
*) die "modo de autostart inválido: $AUTOSTART (use auto|systemd|xdg|profile|none)" ;;
esac

case "$PORT" in
'' | *[!0-9]*) die "porta inválida: $PORT" ;;
esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    die "porta inválida: $PORT (1-65535)"
fi

# --------------------------------------------------------------------------- #
# environment detection
# --------------------------------------------------------------------------- #
SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SETUP_DIR/../.." && pwd)"

OS_NAME="desconhecido"
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    OS_NAME="$(. /etc/os-release && echo "${PRETTY_NAME:-${ID:-Linux}}")"
elif have sw_vers; then
    OS_NAME="macOS $(sw_vers -productVersion)"
fi

IS_WSL=no
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=yes
fi

PKG_MGR=""
if [ "$IS_WSL" = no ] && have sw_vers; then
    have brew && PKG_MGR="brew"
else
    for candidate in apt-get dnf pacman apk zypper; do
        if have "$candidate"; then
            PKG_MGR="$candidate"
            break
        fi
    done
fi

PY_VER=""
PY_OK=no
if have python3; then
    PY_VER="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || true)"
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PY_OK=yes
    fi
fi

VENV_OK=no
if [ "$PY_OK" = yes ] && python3 -c 'import venv, ensurepip' 2>/dev/null && python3 -m venv --help >/dev/null 2>&1; then
    VENV_OK=yes
fi

GUI_OK=no
if { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; } && { have xdg-open || have open; }; then
    GUI_OK=yes
fi

SYSTEMD_USER=no
if have systemctl && systemctl --user show-environment >/dev/null 2>&1; then
    SYSTEMD_USER=yes
fi

HAS_INTEROP=no
if have cmd.exe || have powershell.exe; then
    HAS_INTEROP=yes
fi

# Owner's browser — never the Windows default (Edge). Override with MYDROIDDECK_WIN_BROWSER.
WIN_BROWSER_WIN="${MYDROIDDECK_WIN_BROWSER:-C:\\Desenv\\Util\\Firefox\\firefox.exe}"

report_env() {
    log "Ambiente detectado"
    info "sistema        : $OS_NAME"
    info "WSL            : $IS_WSL"
    info "pré-requisitos : python3=${PY_VER:-ausente} venv=$VENV_OK"
    info "gerenciador    : ${PKG_MGR:-nenhum}"
    info "GUI            : $GUI_OK"
    info "systemd --user : $SYSTEMD_USER"
    info "interop Windows: $HAS_INTEROP"
}

report_env

# --------------------------------------------------------------------------- #
# prerequisites
# --------------------------------------------------------------------------- #
dep_packages() {
    case "$PKG_MGR" in
    apt-get) echo "python3 python3-venv python3-pip" ;;
    dnf) echo "python3 python3-pip" ;;
    pacman) echo "python python-pip" ;;
    apk) echo "python3 py3-pip" ;;
    zypper) echo "python3 python3-pip" ;;
    brew) echo "python3" ;;
    *) echo "" ;;
    esac
}

install_deps() {
    local pkgs
    pkgs="$(dep_packages)"
    [ -n "$pkgs" ] || return 1
    if [ "$(id -u)" != 0 ] && ! have sudo; then
        warn "sudo não encontrado; instale manualmente: $pkgs"
        return 1
    fi
    local sudo=""
    if [ "$(id -u)" != 0 ]; then
        sudo="sudo"
    fi
    # shellcheck disable=SC2086
    case "$PKG_MGR" in
    apt-get) run $sudo apt-get update && run $sudo apt-get install -y $pkgs ;;
    dnf) run $sudo dnf install -y $pkgs ;;
    pacman) run $sudo pacman -Sy --noconfirm $pkgs ;;
    apk) run $sudo apk add $pkgs ;;
    zypper) run $sudo zypper --non-interactive install $pkgs ;;
    brew) run brew install $pkgs ;;
    *) return 1 ;;
    esac
}

ensure_prerequisites() {
    if [ "$PY_OK" = yes ] && [ "$VENV_OK" = yes ]; then
        return 0
    fi

    warn "faltam pré-requisitos (python3 >= 3.10 com venv/pip)."
    local pkgs
    pkgs="$(dep_packages)"
    if [ -n "$pkgs" ]; then
        info "comando sugerido: ${PKG_MGR:-<gerenciador>} install $pkgs"
    fi

    if [ "$INSTALL_DEPS" = 1 ]; then
        install_deps || warn "não consegui instalar os pré-requisitos automaticamente."
        # Re-check.
        if have python3 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PY_OK=yes
            PY_VER="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || true)"
        fi
        if [ "$PY_OK" = yes ] && python3 -c 'import venv, ensurepip' 2>/dev/null; then
            VENV_OK=yes
        fi
    elif [ -t 0 ] && prompt_yes_no "Tentar instalar agora com ${PKG_MGR:-o gerenciador}?" y; then
        INSTALL_DEPS=1
        install_deps || true
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PY_OK=yes
        fi
        if python3 -c 'import venv, ensurepip' 2>/dev/null; then
            VENV_OK=yes
        fi
    fi

    [ "$PY_OK" = yes ] || die "python3 >= 3.10 é obrigatório."
    [ "$VENV_OK" = yes ] || die "o módulo venv (ensurepip) é obrigatório — no Debian/Ubuntu: apt install python3-venv."
}

# --------------------------------------------------------------------------- #
# install location
# --------------------------------------------------------------------------- #
resolve_prefix() {
    if [ -z "$PREFIX" ]; then
        if [ "$ASSUME_YES" = 0 ] && [ -t 0 ]; then
            local answer
            read -r -p "Local de instalação [$DEFAULT_PREFIX]: " answer || answer=""
            PREFIX="${answer:-$DEFAULT_PREFIX}"
        else
            PREFIX="$DEFAULT_PREFIX"
        fi
    fi
    case "$PREFIX" in
    "~") PREFIX="$HOME" ;;
    "~/"*) PREFIX="$HOME/${PREFIX#\~/}" ;;
    esac
    [ -n "$PREFIX" ] || die "local de instalação vazio"
    case "$PREFIX" in
    /*) ;;
    *) die "o local de instalação deve ser um caminho absoluto: $PREFIX" ;;
    esac
}

# --------------------------------------------------------------------------- #
# autostart / shortcuts
# --------------------------------------------------------------------------- #
PROFILE_FILE="$HOME/.profile"
MARK_BEGIN="# >>> MyDroidDeck autostart >>>"
MARK_END="# <<< MyDroidDeck autostart <<<"

profile_remove() {
    [ -f "$PROFILE_FILE" ] || return 0
    grep -qF "$MARK_BEGIN" "$PROFILE_FILE" || return 0
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] remover bloco de autostart de %s\n' "$PROFILE_FILE"
        return 0
    fi
    local tmp
    tmp="$(mktemp)"
    awk -v b="$MARK_BEGIN" -v e="$MARK_END" '
        $0 == b { skip = 1 }
        !skip { print }
        $0 == e { skip = 0 }
    ' "$PROFILE_FILE" >"$tmp"
    mv "$tmp" "$PROFILE_FILE"
}

choose_autostart() {
    case "$AUTOSTART" in
    auto)
        if [ "$SYSTEMD_USER" = yes ]; then
            echo systemd
        elif [ "$IS_WSL" = yes ]; then
            echo profile
        elif [ "$GUI_OK" = yes ]; then
            echo xdg
        else
            echo none
        fi
        ;;
    *) echo "$AUTOSTART" ;;
    esac
}

enable_autostart() { # MODE
    local mode="$1"
    case "$mode" in
    none)
        info "autostart: desativado"
        ;;
    systemd)
        local unit="$HOME/.config/systemd/user/mydroiddeck.service"
        write_file "$unit" <<EOF
[Unit]
Description=$APP_NAME server

[Service]
Type=simple
ExecStart=$BIN/mydroiddeck
WorkingDirectory=$PREFIX/server
Restart=on-failure

[Install]
WantedBy=default.target
EOF
        run systemctl --user daemon-reload || true
        run systemctl --user enable --now mydroiddeck.service || warn "não consegui habilitar o serviço systemd."
        info "autostart: unit systemd --user (mydroiddeck.service)"
        ;;
    xdg)
        write_file "$XDG_AUTOSTART" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Stream Deck controller (server)
Exec=$BIN/mydroiddeck
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
        info "autostart: $XDG_AUTOSTART"
        ;;
    profile)
        profile_remove
        if [ "$DRY_RUN" = 1 ]; then
            printf '[dry-run] acrescentar autostart a %s\n' "$PROFILE_FILE"
        else
            mkdir -p "$PREFIX/logs"
            cat >>"$PROFILE_FILE" <<EOF
$MARK_BEGIN
if [ -x "$BIN/mydroiddeck" ] && ! pgrep -f "$PREFIX/server/launch.py" >/dev/null 2>&1; then
    (setsid nohup "$BIN/mydroiddeck" >>"$PREFIX/logs/server.log" 2>&1 </dev/null &) 2>/dev/null
fi
$MARK_END
EOF
        fi
        info "autostart: $PROFILE_FILE (ao abrir um shell de login)"
        ;;
    esac
}

disable_autostart() {
    profile_remove
    # systemd
    if have systemctl && systemctl --user show-environment >/dev/null 2>&1; then
        run systemctl --user disable --now mydroiddeck.service >/dev/null 2>&1 || true
    fi
    [ "$DRY_RUN" = 1 ] || rm -f "$HOME/.config/systemd/user/mydroiddeck.service"
    # xdg autostart + desktop/applications entries
    [ "$DRY_RUN" = 1 ] || rm -f "$XDG_AUTOSTART"
    [ "$DRY_RUN" = 1 ] || rm -f "$(desktop_dir)/$APP_NAME.desktop"
    [ "$DRY_RUN" = 1 ] || rm -f "$APPS_DIR/$APP_NAME.desktop"
    if [ "$IS_WSL" = yes ] && [ "$HAS_INTEROP" = yes ]; then
        win_shortcut remove || true
    fi
    info "autostart e atalhos removidos."
}

desktop_dir() {
    local dir=""
    if have xdg-user-dir; then
        dir="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    fi
    [ -n "$dir" ] && [ "$dir" != "$HOME" ] || dir="$HOME/Desktop"
    echo "$dir"
}

desktop_entry() { # PATH  EXEC
    write_file "$1" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Stream Deck controller (server)
Exec=$2
Icon=utilities-terminal
Terminal=false
Categories=Utility;Network;
EOF
    run chmod +x "$1"
    if have gio; then
        run gio set "$1" metadata::trusted true >/dev/null 2>&1 || true
    fi
}

# Windows desktop / Start-menu shortcut when running under WSL (the Linux desktop
# is not what the user sees). Delegates to tools/windows-shortcut.ps1 so the
# argument quoting never has to survive a shell round-trip.
win_shortcut() { # add|remove
    local action="$1"
    local helper="$PREFIX/tools/windows-shortcut.ps1"
    local helper_win="$helper"
    if have wslpath; then
        helper_win="$(wslpath -w "$helper" 2>/dev/null || echo "$helper")"
    fi
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] powershell.exe -File %s -Action %s -Target %s\n' "$helper_win" "$action" "$BIN/mydroiddeck-open"
        return 0
    fi
    [ -f "$helper" ] || return 1
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$helper_win" \
        -Action "$action" -Target "$BIN/mydroiddeck-open" -Distro "${WSL_DISTRO_NAME:-}" >/dev/null 2>&1
}

make_shortcuts() {
    if [ "$DESKTOP" = 0 ]; then
        info "atalhos: ignorados (--no-desktop)"
        return 0
    fi
    if [ "$IS_WSL" = yes ] && [ "$HAS_INTEROP" = yes ]; then
        if [ "$GUI_OK" = yes ]; then
            desktop_entry "$(desktop_dir)/$APP_NAME.desktop" "$BIN/mydroiddeck-open"
        fi
        desktop_entry "$APPS_DIR/$APP_NAME.desktop" "$BIN/mydroiddeck-open"
        if win_shortcut add; then
            info "atalhos: Desktop e Menu Iniciar do Windows (via wsl.exe)"
        else
            warn "não consegui criar o atalho do Windows."
        fi
    elif [ "$GUI_OK" = yes ]; then
        desktop_entry "$(desktop_dir)/$APP_NAME.desktop" "$BIN/mydroiddeck-open"
        desktop_entry "$APPS_DIR/$APP_NAME.desktop" "$BIN/mydroiddeck-open"
        info "atalhos: $(desktop_dir) e $APPS_DIR"
    else
        info "atalhos: sem GUI detectada, nada a fazer"
    fi
}

# --------------------------------------------------------------------------- #
# start / open
# --------------------------------------------------------------------------- #
# Open a URL in the owner's browser. Never the Windows default (Edge): under WSL
# launch Firefox explicitly; otherwise use the Linux desktop's browser.
open_url() {
    local url="$1"
    if [ "$IS_WSL" = yes ] && [ "$HAS_INTEROP" = yes ] && have powershell.exe; then
        local mnt=""
        if have wslpath; then
            mnt="$(wslpath -u "$WIN_BROWSER_WIN" 2>/dev/null || true)"
        fi
        if [ -n "$mnt" ] && [ -x "$mnt" ]; then
            if powershell.exe -NoProfile -Command "Start-Process -FilePath '$WIN_BROWSER_WIN' -ArgumentList '$url'" >/dev/null 2>&1; then
                return 0
            fi
        fi
        warn "Firefox não encontrado ($WIN_BROWSER_WIN); tentando o navegador Linux."
    fi
    if have xdg-open; then
        xdg-open "$url" >/dev/null 2>&1 || true
        return 0
    fi
    if have open; then
        open "$url" >/dev/null 2>&1 || true
        return 0
    fi
    warn "abra manualmente: $url"
    return 1
}

start_detached() {
    if have systemctl && systemctl --user show-environment >/dev/null 2>&1; then
        run systemctl --user start mydroiddeck.service >/dev/null 2>&1 || true
        return 0
    fi
    if pgrep -f "$PREFIX/server/launch.py" >/dev/null 2>&1; then
        info "servidor já em execução"
        return 0
    fi
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] iniciar %s em segundo plano\n' "$BIN/mydroiddeck"
        return 0
    fi
    mkdir -p "$PREFIX/logs"
    (setsid nohup "$BIN/mydroiddeck" >>"$PREFIX/logs/server.log" 2>&1 </dev/null &) 2>/dev/null || true
}

wait_healthy() {
    have curl || return 0
    local i
    for ((i = 0; i < 20; i++)); do
        curl -fsS --max-time 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && return 0
        sleep 0.5
    done
    warn "o servidor não respondeu em ~10s; veja $PREFIX/logs/server.log"
}

# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
resolve_prefix
DATA="$PREFIX/data"
VENV="$PREFIX/venv"
BIN="$PREFIX/bin"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
XDG_AUTOSTART="$HOME/.config/autostart/mydroiddeck.desktop"
MODE="$(choose_autostart)"

info "local de instalação: $PREFIX"

if [ "$UNINSTALL" = 1 ]; then
    log "Removendo $APP_NAME"
    disable_autostart
    if [ "$DRY_RUN" = 0 ] && [ -d "$PREFIX" ]; then
        if prompt_yes_no "Apagar também $PREFIX (código, venv e dados)?" n; then
            rm -rf "$PREFIX"
            info "removido: $PREFIX"
        else
            info "mantido: $PREFIX"
        fi
    fi
    log "Pronto."
    exit 0
fi

ensure_prerequisites

log "Instalando em $PREFIX"
run mkdir -p "$PREFIX" "$DATA" "$BIN" "$PREFIX/logs"

# Self-contained: keep the server code next to the venv, so the clone can go away.
copy_server "$PREFIX/server"

if [ "$DRY_RUN" = 1 ]; then
    printf '[dry-run] criar virtualenv em %s\n' "$VENV"
    printf '[dry-run] %s/bin/pip install -e %s/server\n' "$VENV" "$PREFIX"
else
    if [ ! -x "$VENV/bin/python" ]; then
        python3 -m venv "$VENV"
    fi
    "$VENV/bin/pip" install --quiet --upgrade pip || warn "não consegui atualizar o pip."
    "$VENV/bin/pip" install --quiet -e "$PREFIX/server"
fi

write_file "$BIN/mydroiddeck" <<EOF
#!/usr/bin/env bash
# $APP_NAME launcher — honors data/runtime.json (network/port).
set -euo pipefail
export MYDROIDDECK_DATABASE_URL="sqlite:///$DATA/mydroiddeck.db"
export MYDROIDDECK_RUNTIME_CONFIG_FILE="$DATA/runtime.json"
export MYDROIDDECK_ICON_CACHE_DIR="$DATA/icons"
export MYDROIDDECK_ADMIN_AUTH_ENABLED="\${MYDROIDDECK_ADMIN_AUTH_ENABLED:-false}"
cd "$PREFIX/server"
exec "$VENV/bin/python" "$PREFIX/server/launch.py"
EOF
run chmod +x "$BIN/mydroiddeck"

write_file "$BIN/mydroiddeck-open" <<'OPEN_EOF'
#!/usr/bin/env bash
# Start the server if needed and open the Configuration page.
set -euo pipefail

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="$(cd "$BIN_DIR/.." && pwd)"
DATA="$PREFIX/data"
LOG="$PREFIX/logs/server.log"

PORT="$(sed -n 's/.*"port"[[:space:]]*:[[:space:]]*\([0-9]\+\).*/\1/p' "$DATA/runtime.json" 2>/dev/null | head -1)"
PORT="${PORT:-56997}"
URL="http://127.0.0.1:$PORT/"

is_running() { pgrep -f "$PREFIX/server/launch.py" >/dev/null 2>&1; }

if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user start mydroiddeck.service >/dev/null 2>&1 || true
elif ! is_running; then
    mkdir -p "$PREFIX/logs"
    (setsid nohup "$BIN_DIR/mydroiddeck" >>"$LOG" 2>&1 </dev/null &) 2>/dev/null || true
fi

if command -v curl >/dev/null 2>&1; then
    for ((i = 0; i < 20; i++)); do
        curl -fsS --max-time 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break
        sleep 0.5
    done
fi

# Owner's browser — never the Windows default (Edge). Override with MYDROIDDECK_WIN_BROWSER.
WIN_BROWSER="${MYDROIDDECK_WIN_BROWSER:-C:\\Desenv\\Util\\Firefox\\firefox.exe}"
if grep -qi microsoft /proc/version 2>/dev/null || [ -n "${WSL_DISTRO_NAME:-}" ]; then
    if command -v powershell.exe >/dev/null 2>&1; then
        MNT=""
        if command -v wslpath >/dev/null 2>&1; then
            MNT="$(wslpath -u "$WIN_BROWSER" 2>/dev/null || true)"
        fi
        if [ -n "$MNT" ] && [ -x "$MNT" ] &&
            powershell.exe -NoProfile -Command "Start-Process -FilePath '$WIN_BROWSER' -ArgumentList '$URL'" >/dev/null 2>&1; then
            exit 0
        fi
    fi
fi
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
    open "$URL" >/dev/null 2>&1 || true
fi
OPEN_EOF
run chmod +x "$BIN/mydroiddeck-open"

# Deployed helper the installer uses to make the Windows shortcut (see win_shortcut).
write_file "$PREFIX/tools/windows-shortcut.ps1" <<'PS1_EOF'
<#
    Create/remove the MyDroidDeck shortcut on the Windows Desktop and Start menu.
    Called from the Linux/WSL installer; the shortcut runs `wsl.exe` to start the
    server and open the Configuration page.

    Usage:
      powershell -File windows-shortcut.ps1 -Action add -Target <linux-path> [-Distro N]
      powershell -File windows-shortcut.ps1 -Action remove
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('add', 'remove')][string]$Action,
    [string]$Target = '',
    [string]$Distro = ''
)

$ErrorActionPreference = 'Stop'
$Name = 'MyDroidDeck.lnk'
$Paths = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) $Name),
    (Join-Path ([Environment]::GetFolderPath('Programs')) $Name)
)

if ($Action -eq 'remove') {
    foreach ($p in $Paths) { Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
    exit 0
}

if (-not $Target) { throw 'Target is required for -Action add' }
$Wsl = (Get-Command 'wsl.exe' -ErrorAction SilentlyContinue).Source
if (-not $Wsl) { $Wsl = 'wsl.exe' }

if ($Distro) { $Arguments = "-d $Distro -e bash -lc ""exec '$Target'""" }
else { $Arguments = "-e bash -lc ""exec '$Target'""" }

$Shell = New-Object -ComObject WScript.Shell
foreach ($p in $Paths) {
    $Link = $Shell.CreateShortcut($p)
    $Link.TargetPath = $Wsl
    $Link.Arguments = $Arguments
    $Link.Description = 'MyDroidDeck'
    $Link.Save()
}
PS1_EOF

# Seed the runtime config on the first install (keep an existing one).
if [ ! -f "$DATA/runtime.json" ]; then
    if [ "$MODE" = none ]; then
        START_ON_LOGON=false
    else
        START_ON_LOGON=true
    fi
    write_file "$DATA/runtime.json" <<EOF
{
  "visible_on_network": false,
  "port": $PORT,
  "start_on_logon": $START_ON_LOGON
}
EOF
fi

enable_autostart "$MODE"
make_shortcuts

if [ "$START_NOW" = 1 ] || [ "$OPEN_BROWSER" = 1 ]; then
    log "Iniciando o servidor"
    start_detached
    wait_healthy
fi
if [ "$OPEN_BROWSER" = 1 ]; then
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] abrir http://127.0.0.1:%s/ (Firefox)\n' "$PORT"
    else
        open_url "http://127.0.0.1:$PORT/"
    fi
fi

log "Pronto."
info "launcher : $BIN/mydroiddeck"
info "abrir    : $BIN/mydroiddeck-open"
info "config   : http://127.0.0.1:$PORT/"
info "dados    : $DATA"
info "log      : $PREFIX/logs/server.log"
info "autostart: $MODE"
