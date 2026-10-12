"""Password login + signed session cookie for the server-rendered admin UI.

Deliberately dependency-free (like the i18n module): the cookie value is
``<issued_at>.<hmac_sha256>`` signed with ``settings.admin_secret_key``, so no
server-side session store is needed. Sessions expire after
``settings.admin_session_seconds``.

The REST API keeps its per-device bearer tokens; this only gates the HTML pages.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException, Request

from app.core.config import settings

COOKIE_NAME = "mydroiddeck_admin"


def _equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def _signature(payload: str) -> str:
    return hmac.new(
        settings.admin_secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    """Constant-time check of the admin credentials."""
    return _equal(username, settings.admin_user) and _equal(
        password, settings.admin_password
    )


def create_session_token(now: int | None = None) -> str:
    issued = int(time.time() if now is None else now)
    payload = str(issued)
    return f"{payload}.{_signature(payload)}"


def verify_session_token(token: str | None) -> bool:
    """True when ``token`` is well-formed, correctly signed, and unexpired."""
    if not token or "." not in token:
        return False
    payload, _, signature = token.partition(".")
    if not hmac.compare_digest(signature, _signature(payload)):
        return False
    try:
        issued = int(payload)
    except ValueError:
        return False
    return (time.time() - issued) <= settings.admin_session_seconds


def require_admin(request: Request) -> None:
    """Guard for admin pages: send anonymous visitors to the login form.

    A no-login install (``MYDROIDDECK_ADMIN_AUTH_ENABLED=false``) leaves the pages
    open; the REST API still requires a per-device bearer token.
    """
    if not settings.admin_auth_enabled:
        return
    if not verify_session_token(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(
            status_code=303, headers={"Location": "/admin/login"}
        )