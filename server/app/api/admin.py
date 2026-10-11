"""Server-rendered admin UI (Jinja templates + HTML forms).

Strings are localized with the same catalogs as the API, negotiated from
``Accept-Language`` (pt-BR default).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session
from app.i18n.translator import negotiate, translate
from app.models.action import ActionBinding
from app.models.device import Device
from app.models.profile import Button, Profile

router = APIRouter(prefix="/admin", tags=["admin"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _base_context(request: Request) -> dict:
    locale = negotiate(request.headers.get("accept-language"))
    return {"t": lambda key: translate(key, locale), "locale": locale}


def _parse_buttons(raw: str) -> list[Button]:
    """Turn a textarea ('label|action' per line) into ordered buttons."""
    buttons: list[Button] = []
    for index, line in enumerate(line for line in raw.splitlines() if line.strip()):
        label, _, action = line.partition("|")
        buttons.append(
            Button(index=index, label=label.strip(), action=action.strip())
        )
    return buttons


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/admin/profiles", status_code=307)


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
        context={**_base_context(request), "bindings": bindings},
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
    return RedirectResponse(url="/admin/actions", status_code=303)


@router.post("/actions/{action_id}/delete")
def delete_action(
    action_id: int, session: Session = Depends(get_session)
) -> RedirectResponse:
    binding = session.get(ActionBinding, action_id)
    if binding is not None:
        session.delete(binding)
        session.commit()
    return RedirectResponse(url="/admin/actions", status_code=303)
