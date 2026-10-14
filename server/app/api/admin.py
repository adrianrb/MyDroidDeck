"""Server-rendered admin UI (Jinja templates + HTML forms).

Strings are localized with the same catalogs as the API, negotiated from
``Accept-Language`` (pt-BR default).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app import __version__
from app.core.action_examples import load_examples
from app.core.admin_auth import (
    COOKIE_NAME,
    create_session_token,
    require_admin,
    verify_credentials,
)
from app.core.config import settings
from app.core.export_import import (
    ExportError,
    apply_import,
    build_export,
    export_filename,
    export_json,
    export_moment,
    parse_export,
)
from app.core.file_picker import pick_file
from app.core.icons import (
    invalidate_custom_icon,
    invalidate_icon,
    prewarm_icons,
    resolve_icon,
)
from app.core.qr import local_lan_ip, pairing_qr_png, pairing_uri, phone_server_url
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
        "version": __version__,
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


def _ordered_bindings(session: Session) -> list[ActionBinding]:
    """Bindings in admin-defined order (dense sort_order, then creation order)."""
    return list(
        session.scalars(
            select(ActionBinding).order_by(
                ActionBinding.sort_order, ActionBinding.id
            )
        )
    )


def _renumber_actions(session: Session) -> None:
    """Give every binding a dense sort_order matching the current list order."""
    for position, binding in enumerate(_ordered_bindings(session)):
        binding.sort_order = position


def _move_action(session: Session, action_id: int, direction: str) -> bool:
    """Swap ``action_id`` with its neighbor in the admin order (best effort)."""
    ordered = _ordered_bindings(session)
    positions = {binding.id: index for index, binding in enumerate(ordered)}
    index = positions.get(action_id)
    if index is None:
        return False
    neighbor = index - 1 if direction == "up" else index + 1
    if neighbor < 0 or neighbor >= len(ordered):
        return True  # already at the edge: nothing to do, no error
    ordered[index], ordered[neighbor] = ordered[neighbor], ordered[index]
    for position, binding in enumerate(ordered):
        binding.sort_order = position
    return True


def _move_button(profile: Profile, button_id: int, direction: str) -> bool:
    """Swap ``button_id`` with its neighbor inside ``profile`` (by index)."""
    ordered = sorted(profile.buttons, key=lambda button: button.index)
    positions = {button.id: index for index, button in enumerate(ordered)}
    index = positions.get(button_id)
    if index is None:
        return False
    neighbor = index - 1 if direction == "up" else index + 1
    if neighbor < 0 or neighbor >= len(ordered):
        return True
    ordered[index], ordered[neighbor] = ordered[neighbor], ordered[index]
    for position, button in enumerate(ordered):
        button.index = position
    return True


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


def _import_message(request: Request) -> str | None:
    """Localized confirmation for a finished import (counts arrive in the query)."""
    if not request.query_params.get("imported"):
        return None
    locale = negotiate(request.headers.get("accept-language"))

    def count(name: str) -> str:
        value = request.query_params.get(name, "")
        return str(int(value)) if value.isdigit() else "0"

    message = translate("admin.import_ok", locale).format(
        profiles=count("profiles"), actions=count("actions")
    )
    if request.query_params.get("settings"):
        message += translate("admin.import_settings", locale)
    return message


def _config_context(request: Request, **overrides) -> dict:
    """Context for ``config.html``: runtime config plus the flash flags/params."""
    return {
        **_base_context(request),
        "config": load_runtime_config(),
        "error": None,
        "saved": request.query_params.get("saved"),
        "restarted": request.query_params.get("restarted"),
        "usb": request.query_params.get("usb"),
        "import_message": _import_message(request),
        **overrides,
    }


@router.get("/config", response_class=HTMLResponse)
def config_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="config.html", context=_config_context(request)
    )


@router.get("/config/export")
def export_config(session: Session = Depends(get_session)) -> Response:
    """Download the whole configuration as JSON (settings + actions + profiles).

    *Importar…* on the same page reads this file back, so the admin can move the
    whole setup to another install or restore it after wiping the data folder.
    """
    moment = export_moment()
    bundle = build_export(session, load_runtime_config(), __version__, moment)
    return Response(
        content=export_json(bundle),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename(moment)}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/config/import")
async def import_config(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Apply an exported JSON file (upsert by profile name / action key).

    Existing entries keep their ids and pairings; the imported settings (when the
    file carries them) are saved to ``runtime.json`` and the logon helper is
    reconciled, exactly like saving the settings form.
    """
    context = _config_context(request)
    try:
        bundle = parse_export(await file.read())
    except ExportError as exc:
        context["error"] = translate(exc.key, context["locale"])
        return templates.TemplateResponse(
            request=request, name="config.html", context=context, status_code=400
        )
    report = apply_import(session, bundle)
    query = f"imported=1&profiles={report.profiles}&actions={report.actions}"
    if bundle.settings is not None:
        save_runtime_config(
            RuntimeConfig(
                visible_on_network=bundle.settings.visible_on_network,
                port=bundle.settings.port,
                start_on_logon=bundle.settings.start_on_logon,
            )
        )
        _apply_control(
            "enable-logon" if bundle.settings.start_on_logon else "disable-logon"
        )
        query += "&settings=1"
    return RedirectResponse(url=f"/admin/config?{query}", status_code=303)


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
        return templates.TemplateResponse(
            request=request,
            name="config.html",
            context=_config_context(
                request, error=translate("error.invalid_port", context["locale"])
            ),
            status_code=400,
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


@router.post("/config/usb")
def connect_usb() -> RedirectResponse:
    """Ask the host helper to wire the USB cable to the server (``adb reverse``).

    The helper forwards the configured port from the phone to this PC
    (``adb reverse tcp:<port> tcp:<port>``), so the deck reaches the server at
    ``http://127.0.0.1:<port>/`` without using the network. On dev machines
    (no helper) the button is harmless: it only records nothing and redirects.
    """
    _apply_control("usb-connect")
    return RedirectResponse(url="/admin/config?usb=1", status_code=303)


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
        context["profile_rows"] = _parse_buttons(buttons)
        context["buttons_text"] = buttons
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


@router.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
def edit_profile(request: Request, profile_id: int, session: Session = Depends(get_session)):
    profile = session.get(Profile, profile_id)
    if profile is None:
        return RedirectResponse(url="/admin/profiles", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="profiles/form.html",
        context={
            **_base_context(request),
            "profile": profile,
            "buttons_text": "\n".join(
                f"{button.label}|{button.action}"
                for button in sorted(profile.buttons, key=lambda b: b.index)
            ),
            "error": None,
        },
    )


@router.post("/profiles/{profile_id}")
def update_profile(
    request: Request,
    profile_id: int,
    name: str = Form(...),
    locale: str = Form("pt_BR"),
    buttons: str = Form(""),
    session: Session = Depends(get_session),
):
    profile = session.get(Profile, profile_id)
    if profile is None:
        return RedirectResponse(url="/admin/profiles", status_code=303)
    context = _base_context(request)
    context.update(
        {"profile": profile, "buttons_text": buttons, "error": None}
    )
    taken = session.scalar(
        select(Profile).where(Profile.name == name, Profile.id != profile_id)
    )
    if taken:
        context["profile_rows"] = _parse_buttons(buttons)
        context["error"] = translate("error.profile_exists", context["locale"])
        return templates.TemplateResponse(
            request=request, name="profiles/form.html", context=context, status_code=409
        )
    profile.name = name
    profile.locale = locale
    profile.buttons = _parse_buttons(buttons)
    session.commit()
    return RedirectResponse(url="/admin/profiles", status_code=303)


@router.post("/profiles/{profile_id}/buttons/{button_id}/move")
def move_button(
    profile_id: int,
    button_id: int,
    direction: str = Form(...),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """Move a button one position up/down inside its profile (deck order)."""
    profile = session.get(Profile, profile_id)
    if profile is not None:
        _move_button(profile, button_id, direction)
        session.commit()
    return RedirectResponse(url=f"/admin/profiles/{profile_id}/edit", status_code=303)


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
        for binding in _ordered_bindings(session):
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
    """Extract the icons (custom or executable) bound to ``actions`` (best effort)."""
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        bindings = list(
            session.scalars(
                select(ActionBinding).where(ActionBinding.action.in_(actions))
            )
        )
    for binding in bindings:
        try:
            resolve_icon(binding.executable, binding.icon)
        except Exception:  # pragma: no cover - best effort, never breaks the request
            pass


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


def _pairing_context(request: Request) -> dict:
    """QR data for the "pair a new device" page: URL *and* code, as one payload.

    The URL is resolved from the request but swapped to the LAN address when the
    admin page was opened locally, so the QR works from the phone's camera.
    """
    server_url, local_only = phone_server_url(str(request.url), local_lan_ip())
    return {
        "server_url": server_url,
        "pairing_code": settings.pairing_code,
        "pairing_uri": pairing_uri(server_url, settings.pairing_code),
        "local_only": local_only,
    }


@router.get("/devices/pair", response_class=HTMLResponse)
def pair_new_device(request: Request):
    """Show the QR code (server URL + pairing code) the app scans on first run."""
    return templates.TemplateResponse(
        request=request,
        name="devices/pair.html",
        context={**_base_context(request), **_pairing_context(request)},
    )


@router.get("/devices/pair.png")
def pair_new_device_qr(request: Request) -> Response:
    """PNG of the pairing QR (same payload the page shows as text)."""
    server_url, _ = phone_server_url(str(request.url), local_lan_ip())
    return Response(
        content=pairing_qr_png(pairing_uri(server_url, settings.pairing_code)),
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
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
    bindings = _ordered_bindings(session)
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
    _renumber_actions(session)
    session.commit()
    # Extract the icon of every binding in the background (once per program).
    warm = [binding.executable for binding in _ordered_bindings(session)]
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
    icon: str = Form(""),
    session: Session = Depends(get_session),
):
    context = _base_context(request)
    if not action.strip() or not executable.strip():
        context["binding"] = {
            "action": action,
            "executable": executable,
            "args": args,
            "icon": icon,
        }
        context["error"] = translate("error.required", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=400
        )
    if session.scalar(select(ActionBinding).where(ActionBinding.action == action.strip())):
        context["binding"] = {
            "action": action,
            "executable": executable,
            "args": args,
            "icon": icon,
        }
        context["error"] = translate("error.action_exists", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=409
        )
    session.add(
        ActionBinding(
            action=action.strip(),
            executable=executable.strip(),
            args=args.strip(),
            icon=icon.strip() or None,
            sort_order=_new_action_sort_order(session),
        )
    )
    session.commit()
    # The deck draws the program's icon (or the chosen custom one): warm it.
    return RedirectResponse(
        url="/admin/actions",
        status_code=303,
        background=BackgroundTask(_warm_choice, executable.strip(), icon.strip()),
    )


def _new_action_sort_order(session: Session) -> int:
    ordered = _ordered_bindings(session)
    if not ordered:
        return 0
    return max(binding.sort_order for binding in ordered) + 1


def _warm_choice(executable: str, icon: str, refresh: bool = False) -> None:
    """Extract the icon this action will serve (custom path or the exe), best effort.

    With ``refresh`` the cached PNG is dropped first, so a changed executable (or a
    freshly picked file) is re-read from disk and the deck receives the new icon.
    """
    try:
        if refresh:
            if icon.strip():
                invalidate_custom_icon(icon)
            else:
                invalidate_icon(executable)
        resolve_icon(executable, icon)
    except Exception:  # pragma: no cover - best effort, never breaks the request
        pass


@router.get("/actions/{action_id}/edit", response_class=HTMLResponse)
def edit_action(request: Request, action_id: int, session: Session = Depends(get_session)):
    binding = session.get(ActionBinding, action_id)
    if binding is None:
        return RedirectResponse(url="/admin/actions", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="actions/form.html",
        context={**_base_context(request), "binding": binding, "error": None},
    )


@router.post("/actions/{action_id}")
def update_action(
    request: Request,
    action_id: int,
    action: str = Form(""),
    executable: str = Form(""),
    args: str = Form(""),
    icon: str = Form(""),
    session: Session = Depends(get_session),
):
    binding = session.get(ActionBinding, action_id)
    if binding is None:
        return RedirectResponse(url="/admin/actions", status_code=303)
    context = _base_context(request)
    context["binding"] = binding
    if not action.strip() or not executable.strip():
        context["binding"] = {
            "action": action,
            "executable": executable,
            "args": args,
            "icon": icon,
        }
        context["error"] = translate("error.required", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=400
        )
    taken = session.scalar(
        select(ActionBinding).where(
            ActionBinding.action == action.strip(), ActionBinding.id != action_id
        )
    )
    if taken:
        context["binding"] = {
            "action": action,
            "executable": executable,
            "args": args,
            "icon": icon,
        }
        context["error"] = translate("error.action_exists", context["locale"])
        return templates.TemplateResponse(
            request=request, name="actions/form.html", context=context, status_code=409
        )
    # A change to the program or the chosen icon invalidates the cached PNG, so the
    # deck (and the admin preview) picks up the new icon instead of the stale one.
    previous = (binding.executable or "", binding.icon or "")
    binding.action = action.strip()
    binding.executable = executable.strip()
    binding.args = args.strip()
    binding.icon = icon.strip() or None
    session.commit()
    changed = (binding.executable, binding.icon or "") != previous
    return RedirectResponse(
        url="/admin/actions",
        status_code=303,
        background=BackgroundTask(
            _warm_choice, binding.executable, binding.icon or "", changed
        ),
    )


@router.post("/pick-file")
def pick_file_dialog(request: Request, kind: str = "exe") -> JSONResponse:
    """Open a native Windows file dialog and return the chosen path as JSON.

    The server and the browser must be on the same computer (the usual local
    install): the dialog opens on the Windows desktop and the picked path is handed
    back to the form. Dismissing it (or running without a Windows host) answers
    ``{"path": null}``, leaving the field as it was.
    """
    locale = negotiate(request.headers.get("accept-language"))
    if kind == "icon":
        title = translate("admin.pick_icon_title", locale)
        filters = translate("admin.pick_icon_filter", locale)
    else:
        title = translate("admin.pick_exe_title", locale)
        filters = translate("admin.pick_exe_filter", locale)
    return JSONResponse({"path": pick_file(title, filters)})


@router.post("/actions/{action_id}/move")
def move_action(
    action_id: int,
    direction: str = Form(...),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    """Move an action one position up/down in the admin list."""
    _move_action(session, action_id, direction)
    session.commit()
    return RedirectResponse(url="/admin/actions", status_code=303)


@router.get("/icon-preview")
def icon_preview(executable: str = "", icon: str = "") -> FileResponse:
    """Preview the icon a given ``executable``/``icon`` pair resolves to.

    Lets the action form show the *picked* icon before saving (the saved binding is
    previewed by ``GET /admin/actions/{id}/icon``). Answers 404 while nothing is
    extractable — the same resolution the deck sees through ``GET /icon``.
    """
    resolved = resolve_icon(executable, icon)
    if resolved is None:
        raise HTTPException(status_code=404, detail="icon unavailable")
    return FileResponse(resolved, media_type="image/png")


@router.get("/actions/{action_id}/icon")
def action_icon_preview(
    action_id: int, session: Session = Depends(get_session)
) -> FileResponse:
    """Serve the PNG the deck will use for this action (custom or executable icon).

    Lets the admin form preview the icon before saving; answers 404 while there is
    no extractable icon (same resolution the deck sees through ``GET /icon``).
    """
    binding = session.get(ActionBinding, action_id)
    if binding is None:
        return RedirectResponse(url="/admin/actions", status_code=303)
    icon = resolve_icon(binding.executable, binding.icon)
    if icon is None:
        raise HTTPException(status_code=404, detail="icon unavailable")
    return FileResponse(icon, media_type="image/png")


@router.post("/actions/{action_id}/delete")
def delete_action(
    action_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    binding = session.get(ActionBinding, action_id)
    if binding is not None:
        session.delete(binding)
        session.commit()
        _renumber_actions(session)
        session.commit()
    return RedirectResponse(url="/admin/actions", status_code=303)
