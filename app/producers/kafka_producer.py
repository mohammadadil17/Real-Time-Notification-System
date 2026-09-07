import json
from datetime import datetime, timezone

from confluent_kafka import Producer

from app.core.config import settings

EVENTS_TOPIC = "events"

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    return _producer


def publish_event(event_type: str, user_id: int, payload: dict) -> None:
    message = {
        "type": event_type,
        "user_id": user_id,
        "payload": payload,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    producer = get_producer()
    producer.produce(
        EVENTS_TOPIC,
        key=str(user_id).encode(),
        value=json.dumps(message).encode(),
    )
    # Blocking flush keeps the simulate endpoint's response an honest signal that
    # the event actually reached the broker. Fine at demo throughput; a
    # high-throughput producer (e.g. for Locust) would batch instead.
    producer.flush(timeout=5)
