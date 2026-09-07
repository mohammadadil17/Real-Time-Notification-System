import time
import uuid

import redis

from app.core.config import settings
from app.db.redis import redis_client

EVENTS_KEY = "batch:{user_id}:events"
WINDOW_KEY = "batch:{user_id}:window_start"


def add_to_batch(user_id: int, event_id: int) -> None:
    redis_client.rpush(EVENTS_KEY.format(user_id=user_id), event_id)
    # NX: only the first event in a window sets the clock: later events in the
    # same window must not push the deadline back out.
    redis_client.set(WINDOW_KEY.format(user_id=user_id), time.time(), nx=True)


def scan_due_user_ids() -> list[int]:
    # scan_iter, not keys(): KEYS blocks the single-threaded Redis event loop
    # while it walks the whole keyspace; SCAN walks it incrementally instead.
    due = []
    for key in redis_client.scan_iter(match=WINDOW_KEY.format(user_id="*")):
        user_id = int(key.split(":")[1])
        start_ts = redis_client.get(key)
        if start_ts is not None and time.time() - float(start_ts) >= settings.batch_window_seconds:
            due.append(user_id)
    return due


def pop_batch_event_ids(user_id: int) -> list[int]:
    events_key = EVENTS_KEY.format(user_id=user_id)
    window_key = WINDOW_KEY.format(user_id=user_id)
    temp_key = f"{events_key}:flushing:{uuid.uuid4().hex}"

    try:
        # RENAME is a single atomic command: any event pushed after this line
        # lands on a fresh events_key, never lost and never mixed into this
        # batch. The window_start clean-up below is a separate step, so in a
        # rare race a brand-new event's window can inherit the old start
        # time — acceptable: it only means that next batch flushes a little
        # early, never that an event goes missing.
        redis_client.rename(events_key, temp_key)
    except redis.exceptions.ResponseError:
        redis_client.delete(window_key)
        return []

    event_ids = [int(x) for x in redis_client.lrange(temp_key, 0, -1)]
    redis_client.delete(temp_key)
    redis_client.delete(window_key)
    return event_ids
