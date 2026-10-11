"""Profile CRUD. Error messages are localized via ``Accept-Language`` (pt-BR default)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_device
from app.db.session import get_session
from app.i18n.translator import negotiate, translate
from app.models.profile import Button, Profile
from app.schemas.profile import ProfileCreate, ProfileRead

router = APIRouter(
    prefix="/profiles",
    tags=["profiles"],
    dependencies=[Depends(require_device)],
)


@router.get("", response_model=list[ProfileRead])
def list_profiles(session: Session = Depends(get_session)) -> list[Profile]:
    return list(session.scalars(select(Profile).order_by(Profile.id)))


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    session: Session = Depends(get_session),
    accept_language: str | None = Header(default=None),
) -> Profile:
    locale = negotiate(accept_language)
    if session.scalar(select(Profile).where(Profile.name == payload.name)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, translate("error.profile_exists", locale)
        )

    profile = Profile(name=payload.name, locale=payload.locale)
    profile.buttons = [
        Button(index=button.index, label=button.label, action=button.action)
        for button in payload.buttons
    ]
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileRead)
def get_profile(
    profile_id: int,
    session: Session = Depends(get_session),
    accept_language: str | None = Header(default=None),
) -> Profile:
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            translate("error.profile_not_found", negotiate(accept_language)),
        )
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    session: Session = Depends(get_session),
    accept_language: str | None = Header(default=None),
) -> None:
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            translate("error.profile_not_found", negotiate(accept_language)),
        )
    session.delete(profile)
    session.commit()
