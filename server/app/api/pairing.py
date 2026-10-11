"""Device pairing: exchange a shared pairing code for a per-device API token.

``POST /pair`` is intentionally unauthenticated so the app can bootstrap its
credentials. Re-pairing the same device name rotates the token and un-revokes it.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_token, hash_token
from app.db.session import get_session
from app.i18n.translator import negotiate, translate
from app.models.device import Device

router = APIRouter(tags=["pairing"])


class PairRequest(BaseModel):
    code: str
    device_name: str = Field(min_length=1, max_length=120)


class PairResponse(BaseModel):
    token: str
    device_id: int
    name: str


@router.post("/pair", response_model=PairResponse)
def pair(
    payload: PairRequest,
    session: Session = Depends(get_session),
    accept_language: str | None = Header(default=None),
) -> PairResponse:
    locale = negotiate(accept_language)
    if not settings.pairing_code or payload.code != settings.pairing_code:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            translate("error.invalid_pairing_code", locale),
        )

    token = generate_token()
    device = session.scalar(select(Device).where(Device.name == payload.device_name))
    if device is None:
        device = Device(name=payload.device_name, token_hash=hash_token(token))
        session.add(device)
    else:
        device.token_hash = hash_token(token)
        device.revoked = False
    session.commit()
    session.refresh(device)
    return PairResponse(token=token, device_id=device.id, name=device.name)