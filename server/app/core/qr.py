"""Pairing QR helpers shared by the admin UI and the Android app.

The admin page *Dispositivos → Parear novo* draws a QR code the app scans on its
first run to pre-fill the server URL and the pairing code. The payload is a
small URI so it is self-describing and easy to validate on the app side::

    mydroiddeck://pair?url=<percent-encoded base url>&code=<percent-encoded code>

``segno`` (pure Python, MIT) renders the PNG, so the offline Windows bundle
needs no native code or JavaScript to show the code.
"""

from __future__ import annotations

import io
import socket
from urllib.parse import quote, urlsplit

import segno

PAIRING_URI_SCHEME = "mydroiddeck"
PAIRING_URI_TARGET = "pair"

# Hosts only reachable from the machine running the server: a phone scanning the
# QR could never use them, so the page swaps in the LAN address instead.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

# Address used to ask the OS which local IP would route off-box. A UDP
# "connect" sends nothing; it only resolves the route.
_ROUTE_PROBE = ("8.8.8.8", 80)


def pairing_uri(server_url: str, code: str) -> str:
    """Payload encoded in the pairing QR: the server URL plus the pairing code."""
    return (
        f"{PAIRING_URI_SCHEME}://{PAIRING_URI_TARGET}"
        f"?url={quote(server_url, safe='')}&code={quote(code, safe='')}"
    )


def pairing_qr_png(payload: str, scale: int = 8, border: int = 4) -> bytes:
    """Render ``payload`` as a PNG QR code (medium error correction).

    ``border`` keeps the QR spec's 4-module quiet zone, which scanners need to
    lock on when the code is shown on a screen and read from a phone camera.
    """
    buffer = io.BytesIO()
    segno.make(payload, error="m").save(buffer, kind="png", scale=scale, border=border)
    return buffer.getvalue()


def local_lan_ip() -> str | None:
    """Best-effort LAN IPv4 a phone on the same network can reach.

    Returns ``None`` when the host has no usable route (offline machine, tests).
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(_ROUTE_PROBE)
            address = probe.getsockname()[0]
    except OSError:
        return None
    return address or None


def phone_server_url(url: str, lan_ip: str | None) -> tuple[str, bool]:
    """``(base url, local_only)`` the QR should carry, from the admin request URL.

    The admin page is usually opened on the server machine itself, whose host is
    ``127.0.0.1`` — unusable from the phone — so a loopback host is swapped for
    ``lan_ip``. ``local_only`` reports that the swap was impossible, letting the
    page tell the operator to expose the server to the network first.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host in LOOPBACK_HOSTS and lan_ip:
        host = lan_ip
    port = parts.port
    authority = f"{host}:{port}" if port else host
    return f"{parts.scheme}://{authority}/", host in LOOPBACK_HOSTS
