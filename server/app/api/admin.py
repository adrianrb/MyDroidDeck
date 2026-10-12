"""Server-rendered admin UI (Jinja templates + HTML forms).

Strings are localized with the same catalogs as the API, negotiated from
``Accept-Language`` (pt-BR default).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.core.action_examples import load_examples
from app.core.admin_auth import (
    COOKIE_NAME,
    create_session_token,
    require_admin,
    verify_credentials,
)
from app.core.config import settings
from app.core.icons import prewarm_icons
from app.core.runtime_config import (
    RuntimeConfig,
    load_runtime_config,
    save_runtime_config,
    validate_port,
)
from app.db.session import get_session
from app.i18n.translator import negotiate, translate
from app.models.action import ActionBinding
from app.models.device import Device
from app.models.profile import Button, Profile

# Public login/logout routes …
auth_router = APIRouter(prefix="/admin", tags=["admin"])
# … and everything else behind the session guard.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _base_context(request: Request) -> dict:
    locale = negotiate(request.headers.get("accept-language"))
    return {
        "t": lambda key: translate(key, locale),
        "locale": locale,
        "auth_enabled": settings.admin_auth_enabled,
    }


def _parse_buttons(raw: str) -> list[Button]:
    """Turn a textarea ('label|action' per line) into ordered buttons."""
    buttons: list[Button] = []
    for index, line in enumerate(line for line in raw.splitlines() if line.strip()):
        label, _, action = line.partition("|")
        buttons.append(
            Button(index=index, label=label.strip(), action=action.strip())
        )
    return buttons


@auth_router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if not settings.admin_auth_enabled:
        return RedirectResponse(url="/admin/config", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={**_base_context(request), "error": None},
    )


@auth_router.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
):
    if not settings.admin_auth_enabled:
        return RedirectResponse(url="/admin/config", status_code=303)
    if not verify_credentials(username, password):
        context = _base_context(request)
        context["error"] = translate("error.invalid_login", context["locale"])
        return templates.TemplateResponse(
            request=request, name="login.html", context=context, status_code=401
        )
    response = RedirectResponse(url="/admin/profiles", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(),
        httponly=True,
        samesite="lax",
        max_age=settings.admin_session_seconds,
    )
    return response


@auth_router.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/admin/config", status_code=307)


def _apply_control(action: str) -> None:
    """Best-effort call to the installer's control helper (logon task / restart).

    The helper is only present on the installed Windows fork; when it is unset
    (dev machines) the page simply records the preference in runtime.json.
    """
    helper = settings.control_helper.strip()
    if not helper:
        return
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                helper,
                "-Action",
                action,
            ],
            capture_output=True,
            timeout=settings.exec_timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError):
        # Never fail the page because the host helper is unavailable.
        pass


@router.get("/config", response_class=HTMLResponse)
def config_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="config.html",
        context={
            **_base_context(request),
            "config": load_runtime_config(),
            "error": None,
            "saved": request.query_params.get("saved"),
            "restarted": request.query_params.get("restarted"),
        },
    )


@router.post("/config")
def save_config(
    request: Request,
    visible_on_network: str | None = Form(None),
    port: str = Form(""),
    start_on_logon: str | None = Form(None),
):
    context = _base_context(request)
    try:
        port_value = validate_port(port)
    except ValueError:
        context.update(
            {
                "config": load_runtime_config(),
                "error": translate("error.invalid_port", context["locale"]),
                "saved": None,
                "restarted": None,
            }
        )
        return templates.TemplateResponse(
            request=request, name="config.html", context=context, status_code=400
        )

    config = RuntimeConfig(
        visible_on_network=visible_on_network is not None,
        port=port_value,
        start_on_logon=start_on_logon is not None,
    )
    save_runtime_config(config)
    # Reconcile the Windows logon task with the saved preference (best effort).
    _apply_control("enable-logon" if config.start_on_logon else "disable-logon")
    return RedirectResponse(url="/admin/config?saved=1", status_code=303)


@router.post("/config/restart")
def restart_server() -> RedirectResponse:
    """Ask the host helper to restart the server (no-op on dev machines)."""
    _apply_control("restart")
    return RedirectResponse(url="/admin/config?restarted=1", status_code=303)


@router.get("/profiles", response_class=HTMLResponse)
def list_profiles(request: Request, session: Session = Depends(get_session)):
    profiles = list(session.scalars(select(Profile).order_by(Profile.id)))
    return templates.TemplateResponse(
        request=request,
        name="profiles/list.html",
        context={**_base_context(request), "profiles": profiles},
    )


@router.get("/profiles/new", response_class=HTMLResponse)
def new_profile(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="profiles/form.html",
        context={**_base_context(request), "error": None},
    )


@router.post("/profiles")
def create_profile(
    request: Request,
    name: str = Form(...),
    locale: str = Form("pt_BR"),
    buttons: str = Form(""),
    session: Session = Depends(get_session),
):
    context = _base_context(request)
    if session.scalar(select(Profile).where(Profile.name == name)):
        context["error"] = translate("error.profile_exists", context["locale"])
        return templates.TemplateResponse(
            request=request,
            name="profiles/form.html",
            context=context,
            status_code=409,
        )

    profile = Profile(name=name, locale=locale)
    profile.buttons = _parse_buttons(buttons)
    session.add(profile)
    session.commit()
    return RedirectResponse(url="/admin/profiles", status_code=303)


@router.post("/profiles/{profile_id}/delete")
def delete_profile(
    profile_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    profile = session.get(Profile, profile_id)
    if profile is not None:
        session.delete(profile)
        session.commit()
    return RedirectResponse(url="/admin/profiles", status_code=303)


@router.post("/profiles/{profile_id}/examples")
def fill_profile_with_actions(
    profile_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    """Add one button per standard action to ``profile_id`` (idempotent).

    The standard actions are the bindings registered in ``/admin/actions`` (seed
    them with "Importar exemplos"); a button already pointing at an action is kept
    untouched, so the route can be re-run safely to pick up new bindings.
    """
    profile = session.get(Profile, profile_id)
    if profile is not None:
        used = {button.action for button in profile.buttons}
        next_index = max((button.index for button in profile.buttons), default=-1) + 1
        for binding in session.scalars(select(ActionBinding).order_by(ActionBinding.id)):
            if binding.action in used:
                continue
            profile.buttons.append(
                Button(index=next_index, label=binding.action, action=binding.action)
            )
            used.add(binding.action)
            next_index += 1
        session.commit()
        # Warm the icons in the background so the deck's first load is instant.
        warm = [button.action for button in profile.buttons]
        return RedirectResponse(
            url="/admin/profiles",
            status_code=303,
            background=BackgroundTask(_warm_actions, warm),
        )
    return RedirectResponse(url="/admin/profiles", status_code=303)


def _warm_actions(actions: list[str]) -> None:
    """Extract the icons of the executables bound to ``actions`` (best effort)."""
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        executables = [
            binding.executable
            for binding in session.scalars(
                select(ActionBinding).where(ActionBinding.action.in_(actions))
            )
        ]
    prewarm_icons(executables)


@router.get("/devices", response_class=HTMLResponse)
def list_devices(request: Request, session: Session = Depends(get_session)):
    devices = list(session.scalars(select(Device).order_by(Device.id.desc())))
    return templates.TemplateResponse(
        request=request,
        name="devices/list.html",
        context={
            **_base_context(request),
            "devices": devices,
            "pairing_code": settings.pairing_code,
        },
    )


@router.post("/devices/{device_id}/revoke")
def revoke_device(
    device_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    device = session.get(Device, device_id)
    if device is not None:
        device.revoked = True
        session.commit()
    return RedirectResponse(url="/admin/devices", status_code=303)


@router.get("/actions", response_class=HTMLResponse)
def list_actions(request: Request, session: Session = Depends(get_session)):
    bindings = list(session.scalars(select(ActionBinding).order_by(ActionBinding.id)))
    return templates.TemplateResponse(
        request=request,
        name="actions/list.html",
        context={
            **_base_context(request),
            "bindings": bindings,
            "imported": request.query_params.get("imported"),
        },
    )


@router.post("/actions/examples")
def import_example_actions(
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """Seed the example bindings, skipping keys that already exist."""
    existing = set(session.scalars(select(ActionBinding.action)))
    for example in load_examples():
        action = str(example.get("action", "")).strip()
        executable = str(example.get("executable", "")).strip()
        if not action or not executable or action in existing:
            continue
        session.add(
            ActionBinding(
                action=action,
                executable=executable,
                args=str(example.get("args", "")).strip(),
            )
        )
        existing.add(action)
    session.commit()
    # Extract the icon of every binding in the background (once per program).
    warm = list(session.scalars(select(ActionBinding.executable)))
    return RedirectResponse(
        url="/admin/actions?imported=1",
        status_code=303,
        background=BackgroundTask(prewarm_icons, warm),
    )


@router.get("/actions/new", response_class=HTMLResponse)
def new_action(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="actions/form.html",
        context={**_base_context(request), "error": None},
    )


@router.post("/actions")
def create_action(
    request: Request,
    action: str = Form(""),
    executable: str = Form(""),
    args: str = Form(""),
    session: Session = Depends(get_session),
):
    context = _base_context(request)
    if not action.strip() or not executable.strip():
        context["error"] = translate("error.required", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=400
        )
    if session.scalar(select(ActionBinding).where(ActionBinding.action == action.strip())):
        context["error"] = translate("error.action_exists", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=409
        )
    session.add(
        ActionBinding(
            action=action.strip(),
            executable=executable.strip(),
            args=args.strip(),
        )
    )
    session.commit()
    # The deck draws the program's real icon: extract it once, in the background.
    return RedirectResponse(
        url="/admin/actions",
        status_code=303,
        background=BackgroundTask(prewarm_icons, [executable.strip()]),
    )


@router.post("/actions/{action_id}/delete")
def delete_action(
    action_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    binding = session.get(ActionBinding, action_id)
    if binding is not None:
        session.delete(binding)
        session.commit()
    return RedirectResponse(url="/admin/actions", status_code=303)
