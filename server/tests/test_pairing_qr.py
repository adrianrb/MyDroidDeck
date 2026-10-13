"""Pairing QR: payload, PNG round-trip and the admin pages that expose it.

The QR is verified the way the phone sees it: ``segno`` encodes, an independent
decoder (``zxing-cpp``) reads the PNG back, and the payload must be the exact
URI the app parses.
"""

import io
import re

import zxingcpp
from PIL import Image

from app.core.qr import (
    local_lan_ip,
    pairing_qr_png,
    pairing_uri,
    phone_server_url,
)
from app.i18n.translator import translate

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# The TestClient host: not loopback, so pages keep it instead of a LAN address.
TEST_ORIGIN = "http://testserver/"


def _decode(png: bytes) -> str | None:
    result = zxingcpp.read_barcode(Image.open(io.BytesIO(png)).convert("L"))
    return None if result is None else result.text


def test_pairing_uri_carries_the_url_and_the_code():
    assert pairing_uri("http://192.168.100.7:56997/", "pair-dev") == (
        "mydroiddeck://pair"
        "?url=http%3A%2F%2F192.168.100.7%3A56997%2F&code=pair-dev"
    )


def test_pairing_uri_escapes_utf8_and_query_delimiters():
    # A code may contain '+'/'&'/'=' and non-ASCII; all must survive the trip.
    uri = pairing_uri("http://host:56997/", "a+b &ç")
    assert "code=a%2Bb%20%26%C3%A7" in uri
    assert uri.count("&") == 1  # only the url/code separator


def test_pairing_qr_png_is_a_square_png_that_reads_back():
    payload = pairing_uri("http://192.168.100.7:56997/", "pair-dev")
    png = pairing_qr_png(payload)
    assert png.startswith(PNG_MAGIC)
    width, height = Image.open(io.BytesIO(png)).size
    assert width == height > 100
    assert _decode(png) == payload


def test_phone_server_url_swaps_loopback_for_the_lan_address():
    # The admin page is usually opened on the server machine itself.
    assert phone_server_url("http://127.0.0.1:56997/admin/devices/pair", "10.0.0.5") == (
        "http://10.0.0.5:56997/",
        False,
    )
    assert phone_server_url("http://localhost/admin/devices", "10.0.0.5") == (
        "http://10.0.0.5/",
        False,
    )
    # Already a network address: kept as-is.
    assert phone_server_url("http://192.168.0.10:56997/admin/x", "10.0.0.5") == (
        "http://192.168.0.10:56997/",
        False,
    )
    # No LAN address found: the page must warn that this is local-only.
    assert phone_server_url("http://127.0.0.1:56997/admin/devices", None) == (
        "http://127.0.0.1:56997/",
        True,
    )


def test_local_lan_ip_is_none_or_a_dotted_address():
    address = local_lan_ip()
    assert address is None or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", address)


def test_admin_devices_page_offers_to_pair_a_new_device(admin_client):
    listing = admin_client.get("/admin/devices")
    assert 'href="/admin/devices/pair"' in listing.text
    assert translate("admin.pair_new", "pt_BR") in listing.text


def test_pair_page_shows_the_qr_the_url_and_the_code(admin_client):
    response = admin_client.get("/admin/devices/pair")
    assert response.status_code == 200
    assert TEST_ORIGIN in response.text
    assert "pair-dev" in response.text
    assert "/admin/devices/pair.png" in response.text
    # A reachable address: no "this is local-only" warning.
    assert translate("admin.pair_qr_local_only", "pt_BR") not in response.text


def test_pair_qr_png_encodes_the_pairing_uri(admin_client):
    response = admin_client.get("/admin/devices/pair.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert _decode(response.content) == pairing_uri(TEST_ORIGIN, "pair-dev")


def test_pair_qr_is_localized(admin_client):
    response = admin_client.get("/admin/devices/pair", headers={"Accept-Language": "en"})
    assert translate("admin.pair_qr_hint", "en") in response.text
    assert translate("admin.pair_qr_hint", "pt_BR") not in response.text


def test_pair_routes_need_the_admin_session(anon_client):
    for path in ("/admin/devices/pair", "/admin/devices/pair.png"):
        response = anon_client.get(path, follow_redirects=False)
        assert response.status_code == 303, path
        assert response.headers["location"].startswith("/admin/login"), path
