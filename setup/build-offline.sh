#!/usr/bin/env bash
# Assemble the offline Windows bundle that MyDroidDeck.iss packages.
#
# Runs on Linux/WSL: it downloads the *Windows* embeddable Python and installs
# the project's Windows wheels into the runtime's site-packages, then copies the
# server code + launcher into setup/build/stage/.
#
# Resolution uses "uv" (`uv pip install --target --python-platform ...`), because
# plain pip evaluates environment markers for the *host* (breaking packages such
# as uvicorn[standard]/uvloop). uv is reused if present, otherwise installed into
# a throwaway venv under setup/build/.
#
# Usage:
#   setup/build-offline.sh [--python 3.11.9] [--clean] [--no-deps-install]
#
#   --no-deps-install   skip installing wheels (e.g. reusing an existing stage)
#
# Then compile the installer with Inno Setup 6.3+ (ISCC.exe) — see setup/README.md.
set -euo pipefail

PYVER="3.11.9"
CLEAN=0
INSTALL_DEPS=1

while [ $# -gt 0 ]; do
    case "$1" in
    --python) PYVER="$2"; shift 2 ;;
    --clean) CLEAN=1; shift ;;
    --no-deps-install) INSTALL_DEPS=0; shift ;;
    *) echo "opção desconhecida: $1" >&2; exit 2 ;;
    esac
done

SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SETUP_DIR/.." && pwd)"
BUILD="$SETUP_DIR/build"
CACHE="$BUILD/cache"
STAGE="$BUILD/stage"
RUNTIME="$STAGE/runtime"
SITE="$RUNTIME/Lib/site-packages"

PYSHORT="${PYVER%.*}"        # 3.11.9 -> 3.11
PYTAG="python${PYSHORT//./}" # -> python311

for tool in curl unzip; do
    command -v "$tool" >/dev/null 2>&1 || { echo "ferramenta ausente: $tool" >&2; exit 1; }
done

if [ "$CLEAN" = 1 ]; then
    rm -rf "$BUILD"
fi
mkdir -p "$CACHE" "$RUNTIME"

if [ -x "$ROOT/server/.venv/bin/python" ]; then
    PYBIN="$ROOT/server/.venv/bin/python"
else
    PYBIN="python3"
fi

# ---------- 1. Python embeddable distribution (Windows) ----------
EMBED_ZIP="python-$PYVER-embed-amd64.zip"
if [ ! -f "$CACHE/$EMBED_ZIP" ]; then
    echo "Baixando $EMBED_ZIP …"
    curl -fsSL -o "$CACHE/$EMBED_ZIP" \
        "https://www.python.org/ftp/python/$PYVER/$EMBED_ZIP"
fi

rm -rf "$RUNTIME"
mkdir -p "$RUNTIME"
unzip -q -o "$CACHE/$EMBED_ZIP" -d "$RUNTIME"

# The embeddable dist restricts imports through a ._pth file; enable
# site-packages so the vendored wheels become importable.
PTH="$RUNTIME/$PYTAG._pth"
[ -f "$PTH" ] || { echo "esperava $PTH na distribuição embutida" >&2; exit 1; }
{
    echo "$PYTAG.zip"
    echo "."
    echo "Lib\\site-packages"
    echo "import site"
} > "$PTH"

mkdir -p "$SITE"

# ---------- 2. Windows wheels for the server (via uv) ----------
if [ "$INSTALL_DEPS" = 1 ]; then
    UV="$(command -v uv || true)"
    if [ -z "$UV" ]; then
        echo "uv não encontrado; instalando num venv de build …"
        "$PYBIN" -m venv "$BUILD/tools-venv"
        "$BUILD/tools-venv/bin/pip" install --quiet --upgrade pip uv
        UV="$BUILD/tools-venv/bin/uv"
    fi

    echo "Instalando dependências (wheels win_amd64) em site-packages …"
    "$UV" pip install \
        --target "$SITE" \
        --python-platform x86_64-pc-windows-msvc \
        --python-version "$PYSHORT" \
        --no-build \
        --no-cache \
        -r "$SETUP_DIR/requirements-runtime.txt"
fi

# ---------- 3. Server code + launchers ----------
echo "Copiando o servidor e os inicializadores …"
rm -rf "$STAGE/server"
mkdir -p "$STAGE/server"
cp -r "$ROOT/server/app" "$STAGE/server/app"
cp "$ROOT/server/version.txt" "$STAGE/server/version.txt"
cp "$ROOT/server/actions.example.json" "$STAGE/server/actions.example.json"
cp "$ROOT/server/launch.py" "$STAGE/server/launch.py"
cp "$ROOT/server/pyproject.toml" "$STAGE/server/pyproject.toml"
find "$STAGE/server" -type d -name __pycache__ -prune -exec rm -rf {} +

cp "$SETUP_DIR/windows/run-server.cmd" "$STAGE/run-server.cmd"
rm -rf "$STAGE/tools"
cp -r "$SETUP_DIR/windows/tools" "$STAGE/tools"

VERSION="$(tr -d '[:space:]' < "$ROOT/server/version.txt")"
printf 'MyDroidDeck %s\nPython %s (embeddable, win_amd64)\n' "$VERSION" "$PYVER" > "$STAGE/VERSION"

echo
echo "Pronto: $STAGE"
du -sh "$STAGE" 2>/dev/null || true
echo "Compile com:  iscc setup/windows/MyDroidDeck.iss"
