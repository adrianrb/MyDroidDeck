#!/usr/bin/env bash
# Generate the self-signed TLS certificate used by the server, and (unless
# --no-app) copy its public half into the Android app so the deck trusts it.
#
# Usage: deploy/gen-cert.sh [--out DIR] [--days N] [--san DNS:x|IP:y]… [--no-app]
#
# The SAN list always covers localhost/127.0.0.1 and the emulator's host alias
# 10.0.2.2, plus every non-WSL IPv4 of the Windows host (the address a physical
# device uses). Re-run it whenever the LAN IP changes, then rebuild the app.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" # server/
OUT="$ROOT/deploy/tls"
APP_RAW="$ROOT/../app/src/main/res/raw"
DAYS="${MYDROIDDECK_TLS_DAYS:-825}"
EXTRA_SANS=""
COPY_APP=1

while [ $# -gt 0 ]; do
    case "$1" in
    --out)
        OUT="$2"
        shift 2
        ;;
    --days)
        DAYS="$2"
        shift 2
        ;;
    --san)
        EXTRA_SANS="$EXTRA_SANS,$2"
        shift 2
        ;;
    --no-app)
        COPY_APP=0
        shift
        ;;
    *)
        echo "opção desconhecida: $1" >&2
        exit 2
        ;;
    esac
done

# 10.0.2.2 lets the Android emulator reach the host; the LAN IPs cover physical
# devices. Skip the WSL/Hyper-V virtual switch (172.x), unreachable from the phone.
SANS="DNS:localhost,IP:127.0.0.1,IP:10.0.2.2"
if command -v powershell.exe >/dev/null 2>&1; then
    while read -r ip; do
        [ -n "$ip" ] || continue
        case "$ip" in
        172.*) continue ;;
        esac
        SANS="$SANS,IP:$ip"
    done < <(
        powershell.exe -NoProfile -Command \
            "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { \$_.InterfaceAlias -notmatch 'Loopback' }).IPAddress" \
            2>/dev/null | tr -d '\r' | grep -E '^[0-9]' || true
    )
fi
[ -n "$EXTRA_SANS" ] && SANS="$SANS$EXTRA_SANS"

mkdir -p "$OUT"
openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days "$DAYS" \
    -keyout "$OUT/key.pem" -out "$OUT/cert.pem" \
    -subj "/CN=mydroiddeck-dev" \
    -addext "subjectAltName=$SANS" \
    -addext "keyUsage=digitalSignature,keyEncipherment" \
    -addext "extendedKeyUsage=serverAuth" 2>/dev/null
chmod 600 "$OUT/key.pem"

echo "Certificado TLS gerado:"
echo "  cert: $OUT/cert.pem"
echo "  key : $OUT/key.pem (não versionado)"
echo "  SANs: $SANS"

if [ "$COPY_APP" = 1 ]; then
    mkdir -p "$APP_RAW"
    cp "$OUT/cert.pem" "$APP_RAW/mydroiddeck_server.pem"
    echo "  app : $APP_RAW/mydroiddeck_server.pem (confiança do app Android)"
fi
