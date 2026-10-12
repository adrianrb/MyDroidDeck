"""Pydantic schemas for profile/button payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ButtonBase(BaseModel):
    index: int = Field(ge=0)
    label: str
    action: str


class ButtonCreate(ButtonBase):
    pass


class ButtonRead(ButtonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProfileBase(BaseModel):
    name: str
    locale: str = "pt_BR"


class ProfileCreate(ProfileBase):
    buttons: list[ButtonCreate] = Field(default_factory=list)


class ProfileUpdate(ProfileBase):
    buttons: list[ButtonCreate] = Field(default_factory=list)


class ProfileRead(ProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buttons: list[ButtonRead] = Field(default_factory=list)
