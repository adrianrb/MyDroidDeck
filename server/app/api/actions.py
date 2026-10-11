"""REST command dispatch: the app POSTs a button's action here (transport = REST)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["actions"])


class ActionRequest(BaseModel):
    action: str
    label: str | None = None


class ActionResult(BaseModel):
    status: str
    action: str
    executed_at: str


@router.post("/actions", response_model=ActionResult)
def dispatch(request: ActionRequest) -> ActionResult:
    # TODO: execute on the host (OBS/scene switch, shell, ...). For now: acknowledge.
    return ActionResult(
        status="ok",
        action=request.action,
        executed_at=datetime.now(timezone.utc).isoformat(),
    )
