"""REST command dispatch: the app POSTs a button's action here (transport = REST).

The action is executed on the host as a Windows executable, but only when the
admin configured a matching binding (see ``app.core.executor``).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.executor import execute_action
from app.core.icons import extract_icon
from app.core.security import require_device
from app.db.session import get_session
from app.models.action import ActionBinding

router = APIRouter(tags=["actions"], dependencies=[Depends(require_device)])


class ActionRequest(BaseModel):  # noqa: N999 - pydantic schema, not a model
    action: str
    label: str | None = None


class ActionResult(BaseModel):
    status: str
    action: str
    detail: str | None = None
    executed_at: str | None = None


@router.post("/actions", response_model=ActionResult)
def dispatch(
    request: ActionRequest, session: Session = Depends(get_session)
) -> ActionResult:
    """Run the button's action on the host (configured Windows executable)."""
    status, detail = execute_action(request.action, session)
    return ActionResult(
        status=status,
        action=request.action,
        detail=detail,
        executed_at=(
            datetime.now(timezone.utc).isoformat() if status != "unknown" else None
        ),
    )


@router.get("/icon")
def action_icon(action: str, session: Session = Depends(get_session)) -> FileResponse:
    """Serve the real icon (PNG) of the program bound to ``action``.

    The icon is extracted from the Windows executable on first request and cached
    on disk (see ``app.core.icons``). Unknown actions — and programs without an
    extractable icon — answer 404, so the deck keeps showing the text label.
    """
    binding = session.scalar(
        select(ActionBinding).where(ActionBinding.action == action.strip())
    )
    if binding is None:
        raise HTTPException(status_code=404, detail="unknown action")
    icon = extract_icon(binding.executable)
    if icon is None:
        raise HTTPException(status_code=404, detail="icon unavailable")
    return FileResponse(icon, media_type="image/png")