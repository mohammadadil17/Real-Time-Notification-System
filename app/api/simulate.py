import random
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.models.user import User
from app.producers.kafka_producer import publish_event

router = APIRouter(prefix="/simulate", tags=["simulate"])


def _build_payload(event_type: str) -> dict:
    if event_type == "order":
        return {
            "order_id": str(uuid.uuid4()),
            "amount": round(random.uniform(10, 500), 2),
            "status": "placed",
        }
    if event_type == "payment":
        return {
            "payment_id": str(uuid.uuid4()),
            "amount": round(random.uniform(10, 500), 2),
            "status": "success",
        }
    return {
        "delivery_id": str(uuid.uuid4()),
        "status": random.choice(["out_for_delivery", "delivered"]),
    }


@router.post("/{event_type}", status_code=status.HTTP_202_ACCEPTED)
def simulate_event(
    event_type: Literal["order", "payment", "delivery"],
    current_user: User = Depends(get_current_user),
) -> dict:
    payload = _build_payload(event_type)
    publish_event(event_type=event_type, user_id=current_user.id, payload=payload)
    return {"status": "published", "type": event_type, "payload": payload}
