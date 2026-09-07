from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .where(Event.user_id == current_user.id)
            .order_by(Event.occurred_at.desc())
        ).all()
    )
