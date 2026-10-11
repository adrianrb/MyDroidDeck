"""TLS configuration: the settings flag and the certificate generator script."""

from __future__ import annotations

import shutil
import ssl
import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings

SERVER_DIR = Path(__file__).resolve().parents[1]


def test_tls_enabled_requires_both_paths():
    assert Settings(ssl_certfile="", ssl_keyfile="").tls_enabled is False
    assert Settings(ssl_certfile="cert.pem", ssl_keyfile="").tls_enabled is False
    assert Settings(ssl_certfile="", ssl_keyfile="key.pem").tls_enabled is False
    assert Settings(ssl_certfile="cert.pem", ssl_keyfile="key.pem").tls_enabled is True


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl indisponível")
def test_gen_cert_script_produces_a_usable_certificate(tmp_path):
    script = SERVER_DIR / "deploy" / "gen-cert.sh"
    subprocess.run(
        [
            "bash",
            str(script),
            "--out",
            str(tmp_path),
            "--no-app",
            "--san",
            "IP:203.0.113.9",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    assert cert.is_file() and key.is_file()

    # Python's TLS stack must accept the generated pair …
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert), keyfile=str(key))

    # … and the SANs must include the emulator alias and the extra IP we passed.
    details = subprocess.run(
        ["openssl", "x509", "-in", str(cert), "-noout", "-ext", "subjectAltName"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "10.0.2.2" in details
    assert "203.0.113.9" in details
