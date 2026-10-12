#!/usr/bin/env bash
# Smoke tests for setup/linux/install-server.sh (the Linux/WSL installer).
#
# Never touches the real HOME or installs anything: the cases use --dry-run or
# read the script statically. Run it from anywhere:
#
#   setup/tests/test-install-server.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="$HERE/../linux/install-server.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ok() { printf 'ok   - %s\n' "$1"; pass=$((pass + 1)); }
bad() { printf 'FAIL - %s\n' "$1" >&2; fail=$((fail + 1)); }

# 1. Valid bash syntax.
if bash -n "$INSTALLER"; then ok "sintaxe bash"; else bad "sintaxe bash"; fi

# 2. --help exits 0 and documents the main options.
if out="$("$INSTALLER" --help 2>&1)" &&
    grep -q -- "--prefix" <<<"$out" &&
    grep -q -- "--autostart" <<<"$out" &&
    grep -q -- "--uninstall" <<<"$out"; then
    ok "--help"
else
    bad "--help"
fi

# 3. --dry-run prints the plan and creates nothing.
out="$("$INSTALLER" --dry-run --prefix "$TMP/prefix" --no-open --no-start \
    --no-desktop --autostart none --yes 2>&1)"
if grep -q "dry-run" <<<"$out" && [ ! -e "$TMP/prefix" ]; then
    ok "dry-run não cria nada"
else
    bad "dry-run não cria nada"
fi

# 4. Rejects an out-of-range port.
if "$INSTALLER" --dry-run --port 70000 --prefix "$TMP/p" --autostart none --yes >/dev/null 2>&1; then
    bad "porta inválida rejeitada"
else
    ok "porta inválida rejeitada"
fi

# 5. Rejects an unknown option.
if "$INSTALLER" --nope >/dev/null 2>&1; then
    bad "opção desconhecida rejeitada"
else
    ok "opção desconhecida rejeitada"
fi

# 6. Never opens the Windows default browser (only Firefox).
if grep -q "Firefox" "$INSTALLER"; then
    ok "navegador: Firefox"
else
    bad "navegador: Firefox"
fi
if grep -Fq "Start-Process '\$URL'" "$INSTALLER" || grep -Fq 'cmd.exe /c start "" "$URL"' "$INSTALLER"; then
    bad "não usa o navegador padrão do Windows"
else
    ok "não usa o navegador padrão do Windows"
fi

printf '\n%d ok, %d falhas\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
