"""REST command dispatch: the app POSTs a button's action here (transport = REST).

The action is executed on the host as a Windows executable, but only when the
admin configured a matching binding (see ``app.core.executor``).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.executor import execute_action
from app.core.security import require_device
from app.db.session import get_session

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