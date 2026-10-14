#!/usr/bin/env bash
# MyDroidDeck server installer for Linux and WSL — the "Linux/WSL" fork.
#
# Per-user and self-contained: installs under $HOME/MyDroidDeck by default (no root
# needed), creates a virtualenv, seeds data/runtime.json (no login, port 56997) and,
# optionally, autostarts the server at logon and adds shortcuts for Configuração /
# start / stop / restart / readme.txt. On WSL it opens the Configuration page in the
# Windows browser and creates the shortcuts in the Windows Start menu.
#
# Usage: setup/linux/install-server.sh [options]
#   --prefix DIR        install location (default: $HOME/MyDroidDeck)
#   --port N            TCP port (default: 56997)
#   --connectivity LIST how the phone reaches the server: usb,wifi (default),
#                       usb, wifi or none. Without it, asks when interactive.
#   --autostart MODE    auto|systemd|xdg|profile|none (default: auto)
#   --no-desktop        skip the desktop / Start-menu shortcuts
#   --no-open           do not open the browser
#   --no-start          do not start the server now
#   --install-deps      install missing prerequisites with sudo (asks first)
#   --yes               non-interactive: keep every default
#   --uninstall         remove the autostart entry and shortcuts, then exit
#   --dry-run           print what would be done; change nothing
#   -h, --help          this help
#
# After install, control the server with:  bin/mydroiddeck start|stop|restart|status
set -euo pipefail

APP_NAME="MyDroidDeck"
DEFAULT_PORT=56997
DEFAULT_PREFIX="$HOME/MyDroidDeck"

PREFIX=""
PORT="$DEFAULT_PORT"
# Connectivity (like the Windows wizard): USB (adb reverse over the cable) and
# Wi-Fi/LAN (server visible on the network). Bluetooth has no transport yet.
# Default mirrors the wizard's pre-checked boxes (USB + Wi-Fi).
CONNECT="usb,wifi"
CONNECT_SPECIFIED=0
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
    --connectivity)
        [ $# -ge 2 ] || die "--connectivity exige um valor"
        CONNECT="$2"
        CONNECT_SPECIFIED=1
        shift 2
        ;;
    --connectivity=*)
        CONNECT="${1#*=}"
        CONNECT_SPECIFIED=1
        shift
        ;;
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
        sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *) die "opção desconhecida: $1" ;;
    esac
done

case "$AUTOSTART" in
auto | systemd | xdg | profile | none) ;;
*) die "modo de autostart inválido: $AUTOSTART (use auto|systemd|xdg|profile|none)" ;;
esac

# Connectivity: "usb", "wifi", both (any order) or "none". Membership is a plain
# comma-list so bin/mydroiddeck can ask the question the same way.
connect_has() { # usb|wifi
    case ",$CONNECT," in *",$1,"*) return 0 ;; esac
    return 1
}

resolve_connectivity() { # SPEC
    local spec="$1" out="" item
    local IFS=,
    for item in $spec; do
        case "$item" in
        usb | wifi | none | '') ;;
        *) die "conectividade inválida: $item (use usb,wifi|usb|wifi|none)" ;;
        esac
    done
    case ",$spec," in *,usb,*) out="usb" ;; esac
    case ",$spec," in *,wifi,*) out="${out:+$out,}wifi" ;; esac
    CONNECT="$out"
}

# Offer the choices like the Windows wizard (USB and Wi-Fi pre-selected). Only
# when --connectivity was not given, an interactive shell is attached and the
# user did not ask for --yes.
choose_connectivity() {
    if [ "$CONNECT_SPECIFIED" = 1 ]; then
        resolve_connectivity "$CONNECT"
    elif [ "$ASSUME_YES" = 0 ] && [ -t 0 ]; then
        local want_usb=1 want_wifi=1
        printf 'Como o celular vai falar com este servidor?\n'
        prompt_yes_no "  USB (cabo, adb reverse)" y || want_usb=0
        prompt_yes_no "  Wi-Fi (visível na rede local)" y || want_wifi=0
        CONNECT=""
        [ "$want_usb" = 1 ] && CONNECT="usb"
        [ "$want_wifi" = 1 ] && CONNECT="${CONNECT:+$CONNECT,}wifi"
    fi
    return 0
}

connect_description() {
    if [ -z "$CONNECT" ]; then
        echo "nenhuma (somente este PC, 127.0.0.1)"
        return
    fi
    local out=""
    connect_has usb && out="USB"
    connect_has wifi && out="${out:+$out + }Wi-Fi"
    echo "$out"
}

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
    # xdg autostart + the desktop / applications entries (config/start/stop/restart/readme)
    [ "$DRY_RUN" = 1 ] || rm -f "$XDG_AUTOSTART"
    local d s
    for d in "$APPS_DIR" "$(desktop_dir)"; do
        for s in config start stop restart readme usb; do
            [ "$DRY_RUN" = 1 ] || rm -f "$d/mydroiddeck-$s.desktop"
        done
        [ "$DRY_RUN" = 1 ] || rm -f "$d/$APP_NAME.desktop"
    done
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

desktop_entry() { # PATH  NAME  SUBCOMMAND
    write_file "$1" <<EOF
[Desktop Entry]
Type=Application
Name=$2
Comment=Stream Deck controller (server)
Exec="$BIN/mydroiddeck" $3
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
    local connect_arg=""
    local -a args=()
    if have wslpath; then
        helper_win="$(wslpath -w "$helper" 2>/dev/null || echo "$helper")"
    fi
    args=(-Action "$action" -Prefix "$PREFIX" -Distro "${WSL_DISTRO_NAME:-}")
    if connect_has usb; then
        args+=(-ConnectUsb)
        connect_arg=" -ConnectUsb"
    fi
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] powershell.exe -File %s -Action %s -Prefix %s%s\n' \
            "$helper_win" "$action" "$PREFIX" "$connect_arg"
        return 0
    fi
    [ -f "$helper" ] || return 1
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$helper_win" \
        "${args[@]}" >/dev/null 2>&1
}

make_shortcuts() {
    if [ "$DESKTOP" = 0 ]; then
        info "atalhos: ignorados (--no-desktop)"
        return 0
    fi

    local with_gui=0 with_win=0
    [ "$GUI_OK" = yes ] && with_gui=1
    if [ "$IS_WSL" = yes ] && [ "$HAS_INTEROP" = yes ]; then with_win=1; fi

    # Desktop icon (only when a GUI is actually visible).
    if [ "$with_gui" = 1 ]; then
        desktop_entry "$(desktop_dir)/mydroiddeck-config.desktop" "Configuração" open
        # USB helper, only when USB connectivity was chosen.
        if connect_has usb; then
            desktop_entry "$(desktop_dir)/mydroiddeck-usb.desktop" "Conectar por USB" usb
        fi
    fi

    # Application-menu entries: Configuração / start / stop / restart / readme.
    if [ "$with_gui" = 1 ] || [ "$with_win" = 1 ]; then
        desktop_entry "$APPS_DIR/mydroiddeck-config.desktop" "Configuração" open
        desktop_entry "$APPS_DIR/mydroiddeck-start.desktop" "Iniciar servidor" start
        desktop_entry "$APPS_DIR/mydroiddeck-stop.desktop" "Parar servidor" stop
        desktop_entry "$APPS_DIR/mydroiddeck-restart.desktop" "Reiniciar servidor" restart
        desktop_entry "$APPS_DIR/mydroiddeck-readme.desktop" "readme.txt" readme
        if connect_has usb; then
            desktop_entry "$APPS_DIR/mydroiddeck-usb.desktop" "Conectar por USB" usb
        fi
    fi

    if [ "$with_win" = 1 ]; then
        if win_shortcut add; then
            info "atalhos: Menu Iniciar do Windows + $APPS_DIR"
        else
            warn "não consegui criar os atalhos do Windows."
        fi
    elif [ "$with_gui" = 1 ]; then
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
    if [ "$DRY_RUN" = 1 ]; then
        printf '[dry-run] iniciar %s em segundo plano\n' "$BIN/mydroiddeck"
        return 0
    fi
    "$BIN/mydroiddeck" start
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

choose_connectivity
info "conectividade: $(connect_description)"

ensure_prerequisites

log "Instalando em $PREFIX"
run mkdir -p "$PREFIX" "$DATA" "$BIN" "$PREFIX/logs"

# Self-contained: keep the server code next to the venv, so the clone can go away.
copy_server "$PREFIX/server"

# Usage notes (readme.txt) shipped next to the server.
if [ -f "$ROOT/setup/readme.txt" ]; then
    run cp "$ROOT/setup/readme.txt" "$PREFIX/readme.txt"
fi

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

write_file "$BIN/mydroiddeck" <<'MD_EOF'
#!/usr/bin/env bash
# MyDroidDeck server control — run | start | stop | restart | status | open | readme | usb
#
#   (no argument) / run   run the server in the foreground (used by systemd)
#   start                 start it in the background (systemd --user if available)
#   stop                  stop it
#   restart               stop, then start
#   status                is it running, and which version?
#   open                  start it if needed and open the Configuration page
#   readme                open readme.txt
#   usb                   forward the port over the USB cable (adb reverse)
#   usb-off               undo the USB port forwarding
set -euo pipefail

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="$(cd "$BIN_DIR/.." && pwd)"
DATA="$PREFIX/data"
LOG="$PREFIX/logs/server.log"
VENV="$PREFIX/venv"
LAUNCH="$PREFIX/server/launch.py"

PORT="$(sed -n 's/.*"port"[[:space:]]*:[[:space:]]*\([0-9]\+\).*/\1/p' "$DATA/runtime.json" 2>/dev/null | head -1)"
PORT="${PORT:-56997}"
URL="http://127.0.0.1:$PORT/"

have() { command -v "$1" >/dev/null 2>&1; }
is_running() { pgrep -f "$LAUNCH" >/dev/null 2>&1; }
has_systemd() { have systemctl && systemctl --user show-environment >/dev/null 2>&1; }

run_foreground() {
    export MYDROIDDECK_DATABASE_URL="sqlite:///$DATA/mydroiddeck.db"
    export MYDROIDDECK_RUNTIME_CONFIG_FILE="$DATA/runtime.json"
    export MYDROIDDECK_ICON_CACHE_DIR="$DATA/icons"
    export MYDROIDDECK_ADMIN_AUTH_ENABLED="${MYDROIDDECK_ADMIN_AUTH_ENABLED:-false}"
    cd "$PREFIX/server"
    exec "$VENV/bin/python" "$LAUNCH"
}

wait_healthy() {
    have curl || return 0
    local i
    for ((i = 0; i < 20; i++)); do
        curl -fsS --max-time 1 "${URL}health" >/dev/null 2>&1 && return 0
        sleep 0.5
    done
    return 1
}

start_server() {
    if has_systemd; then
        systemctl --user start mydroiddeck.service >/dev/null 2>&1 || true
        return 0
    fi
    if is_running; then
        echo "servidor já em execução"
        return 0
    fi
    mkdir -p "$PREFIX/logs"
    (setsid nohup "$BIN_DIR/mydroiddeck" >>"$LOG" 2>&1 </dev/null &) 2>/dev/null || true
    echo "servidor iniciado"
}

stop_server() {
    local was=0
    if has_systemd; then
        systemctl --user stop mydroiddeck.service >/dev/null 2>&1 && was=1 || true
    fi
    if is_running; then
        pkill -f "$LAUNCH" >/dev/null 2>&1 && was=1 || true
        sleep 0.5
    fi
    if [ "$was" = 1 ]; then echo "servidor parado"; else echo "servidor não está em execução"; fi
}

# Owner's browser — never the Windows default (Edge). Override with MYDROIDDECK_WIN_BROWSER.
open_url() {
    local url="$1"
    local win_browser="${MYDROIDDECK_WIN_BROWSER:-C:\\Desenv\\Util\\Firefox\\firefox.exe}"
    if { [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; } && have powershell.exe; then
        local mnt=""
        if have wslpath; then
            mnt="$(wslpath -u "$win_browser" 2>/dev/null || true)"
        fi
        if [ -n "$mnt" ] && [ -x "$mnt" ] &&
            powershell.exe -NoProfile -Command "Start-Process -FilePath '$win_browser' -ArgumentList '$url'" >/dev/null 2>&1; then
            return 0
        fi
    fi
    if have xdg-open; then xdg-open "$url" >/dev/null 2>&1 && return 0; fi
    if have open; then open "$url" >/dev/null 2>&1 && return 0; fi
    echo "abra manualmente: $url"
    return 1
}

open_readme() {
    local readme="$PREFIX/readme.txt"
    [ -f "$readme" ] || readme="$PREFIX/server/README.md"
    if have powershell.exe && have wslpath; then
        local win
        win="$(wslpath -w "$readme" 2>/dev/null || true)"
        if [ -n "$win" ] && powershell.exe -NoProfile -Command "Start-Process -FilePath 'notepad.exe' -ArgumentList '$win'" >/dev/null 2>&1; then
            return 0
        fi
    fi
    if have xdg-open; then xdg-open "$readme" >/dev/null 2>&1 && return 0; fi
    if have open; then open "$readme" >/dev/null 2>&1 && return 0; fi
    echo "$readme"
}

# adb comes from the Android SDK platform-tools (adb.exe when this runs under WSL).
resolve_adb() {
    local candidate
    for candidate in adb adb.exe; do
        if have "$candidate"; then
            command -v "$candidate"
            return 0
        fi
    done
    local sdk
    for sdk in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}"; do
        if [ -n "$sdk" ] && [ -x "$sdk/platform-tools/adb" ]; then
            echo "$sdk/platform-tools/adb"
            return 0
        fi
        if [ -n "$sdk" ] && [ -x "$sdk/platform-tools/adb.exe" ]; then
            echo "$sdk/platform-tools/adb.exe"
            return 0
        fi
    done
    return 1
}

# USB cable: forward the server port from the phone to this machine, so the app
# reaches the server at http://127.0.0.1:<port>/ with no network at all.
connect_usb() {
    local adb
    if ! adb="$(resolve_adb)"; then
        echo "adb nao encontrado (instale o Android SDK platform-tools)." >&2
        return 1
    fi
    if ! is_running; then start_server >/dev/null; fi
    "$adb" reverse "tcp:$PORT" "tcp:$PORT" >/dev/null
    echo "adb reverse tcp:$PORT tcp:$PORT"
    echo "no app, use: $URL"
}

disconnect_usb() {
    local adb
    if ! adb="$(resolve_adb)"; then
        echo "adb nao encontrado." >&2
        return 1
    fi
    "$adb" reverse --remove "tcp:$PORT" >/dev/null 2>&1 || true
    echo "adb reverse --remove tcp:$PORT"
}

case "${1:-run}" in
run) run_foreground ;;
start) start_server ;;
stop) stop_server ;;
restart)
    stop_server
    start_server
    ;;
status)
    if is_running; then
        echo "servidor em execução na porta $PORT"
        if have curl; then
            curl -fsS --max-time 2 "${URL}health" 2>/dev/null || true
            echo
        fi
    else
        echo "servidor parado"
    fi
    ;;
open)
    start_server
    wait_healthy || echo "aviso: o servidor não respondeu em ~10s; veja $LOG" >&2
    open_url "$URL"
    ;;
readme) open_readme ;;
usb) connect_usb ;;
usb-off) disconnect_usb ;;
-h | --help | help)
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    ;;
*)
    echo "uso: myroiddeck [run|start|stop|restart|status|open|readme]" >&2
    exit 2
    ;;
esac
MD_EOF
run chmod +x "$BIN/mydroiddeck"

write_file "$BIN/mydroiddeck-open" <<'OPEN_EOF'
#!/usr/bin/env bash
# Start the server if needed and open the Configuration page.
# Kept for backwards compatibility: same as `mydroiddeck open`.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mydroiddeck" open
OPEN_EOF
run chmod +x "$BIN/mydroiddeck-open"

# Deployed helper the installer uses to make the Windows shortcuts (see win_shortcut).
write_file "$PREFIX/tools/windows-shortcut.ps1" <<'PS1_EOF'
<#
    Create/remove the MyDroidDeck shortcuts on the Windows Desktop and Start menu.
    Called from the Linux/WSL installer; each shortcut runs `wsl.exe` into the
    distro and runs the matching bin/mydroiddeck subcommand.

    Usage:
      powershell -File windows-shortcut.ps1 -Action add -Prefix <linux-prefix> [-Distro N] [-ConnectUsb]
      powershell -File windows-shortcut.ps1 -Action remove

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 reads .ps1 files
    without a BOM using the system ANSI codepage).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('add', 'remove')][string]$Action,
    [string]$Prefix = '',
    [string]$Distro = '',
    [switch]$ConnectUsb
)

$ErrorActionPreference = 'Stop'

# Shortcut name -> bin/mydroiddeck subcommand.
$Entries = @(
    @{ Name = 'Configuracao do MyDroidDeck'; Sub = 'open' },
    @{ Name = 'Iniciar servidor MyDroidDeck'; Sub = 'start' },
    @{ Name = 'Parar servidor MyDroidDeck'; Sub = 'stop' },
    @{ Name = 'Reiniciar servidor MyDroidDeck'; Sub = 'restart' },
    @{ Name = 'readme.txt'; Sub = 'readme' }
)
if ($ConnectUsb) {
    $Entries += @{ Name = 'Conectar por USB'; Sub = 'usb' }
}
$MenuDir = Join-Path ([Environment]::GetFolderPath('Programs')) 'MyDroidDeck'
$DesktopMain = Join-Path ([Environment]::GetFolderPath('Desktop')) 'MyDroidDeck.lnk'

if ($Action -eq 'remove') {
    Remove-Item -LiteralPath $DesktopMain -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $MenuDir) {
        Remove-Item -LiteralPath $MenuDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    exit 0
}

if (-not $Prefix) { throw 'Prefix is required for -Action add' }

$Wsl = (Get-Command 'wsl.exe' -ErrorAction SilentlyContinue).Source
if (-not $Wsl) { $Wsl = 'wsl.exe' }

$Bin = "$Prefix/bin/mydroiddeck"
function Get-WslArguments([string]$Sub) {
    $Command = "exec '$Bin' $Sub"
    if ($Distro) { return "-d $Distro -e bash -lc ""$Command""" }
    return "-e bash -lc ""$Command"""
}

$Shell = New-Object -ComObject WScript.Shell
if (-not (Test-Path -LiteralPath $MenuDir)) { New-Item -ItemType Directory -Path $MenuDir -Force | Out-Null }

foreach ($Entry in $Entries) {
    $Path = Join-Path $MenuDir ($Entry.Name + '.lnk')
    $Link = $Shell.CreateShortcut($Path)
    $Link.TargetPath = $Wsl
    $Link.Arguments = (Get-WslArguments $Entry.Sub)
    $Link.Description = 'MyDroidDeck'
    $Link.Save()
}

# A single main shortcut on the Desktop (opens the Configuration page).
$Main = $Shell.CreateShortcut($DesktopMain)
$Main.TargetPath = $Wsl
$Main.Arguments = (Get-WslArguments 'open')
$Main.Description = 'MyDroidDeck'
$Main.Save()
PS1_EOF

# Seed the runtime config on the first install (keep an existing one).
if [ ! -f "$DATA/runtime.json" ]; then
    if [ "$MODE" = none ]; then
        START_ON_LOGON=false
    else
        START_ON_LOGON=true
    fi
    # Wi-Fi/LAN: the server must listen on the network, not only on 127.0.0.1.
    if connect_has wifi; then
        VISIBLE_ON_NETWORK=true
    else
        VISIBLE_ON_NETWORK=false
    fi
    write_file "$DATA/runtime.json" <<EOF
{
  "visible_on_network": $VISIBLE_ON_NETWORK,
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
info "controle : $BIN/mydroiddeck start|stop|restart|status"
info "abrir    : $BIN/mydroiddeck-open"
info "config   : http://127.0.0.1:$PORT/"
info "dados    : $DATA"
info "log      : $PREFIX/logs/server.log"
info "autostart: $MODE"
info "conectividade: $(connect_description)"
