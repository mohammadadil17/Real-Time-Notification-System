from sqlalchemy import select

from app.ai.digest import generate_digest
from app.db.session import SessionLocal
from app.models.event import Event
from app.models.notification import Notification
from app.services.batching import pop_batch_event_ids


def flush_user_batch(user_id: int) -> Notification | None:
    event_ids = pop_batch_event_ids(user_id)
    if not event_ids:
        return None

    db = SessionLocal()
    try:
        events = list(db.scalars(select(Event).where(Event.id.in_(event_ids))).all())
        if not events:
            return None

        message = generate_digest(events)
        notification = Notification(user_id=user_id, message=message)
        db.add(notification)
        db.flush()  # populate notification.id before linking events to it

        for event in events:
            event.notification_id = notification.id

        db.commit()
        db.refresh(notification)
        return notification
    finally:
        db.close()
