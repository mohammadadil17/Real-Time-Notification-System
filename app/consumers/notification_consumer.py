import json
import signal
import sys
from datetime import datetime

from confluent_kafka import Consumer

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.event import Event
from app.producers.kafka_producer import EVENTS_TOPIC

GROUP_ID = "notification-consumer"


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def handle_message(db, raw_value: bytes) -> None:
    data = json.loads(raw_value)
    event = Event(
        user_id=data["user_id"],
        type=data["type"],
        payload=data["payload"],
        occurred_at=datetime.fromisoformat(data["occurred_at"]),
    )
    db.add(event)
    db.commit()


def run() -> None:
    consumer = build_consumer()
    consumer.subscribe([EVENTS_TOPIC])
    print(f"[notification-consumer] subscribed to '{EVENTS_TOPIC}', group='{GROUP_ID}'", flush=True)

    running = True

    def _shutdown(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"[notification-consumer] error: {msg.error()}", file=sys.stderr, flush=True)
                continue

            db = SessionLocal()
            try:
                handle_message(db, msg.value())
            except Exception as exc:
                db.rollback()
                # Skip committing so this offset is redelivered on restart, rather
                # than crashing the whole consumer over one bad message.
                print(f"[notification-consumer] failed to process message: {exc}", file=sys.stderr, flush=True)
            else:
                consumer.commit(message=msg)
                data = json.loads(msg.value())
                print(
                    f"[notification-consumer] stored event user_id={data['user_id']} type={data['type']}",
                    flush=True,
                )
            finally:
                db.close()
    finally:
        consumer.close()


if __name__ == "__main__":
    run()
