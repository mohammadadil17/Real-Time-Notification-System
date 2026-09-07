import json

from app.db.redis import redis_client

NOTIFICATIONS_CACHE_KEY = "cache:notifications:{user_id}"
NOTIFICATIONS_CACHE_TTL_SECONDS = 30


def get_cached_notifications(user_id: int) -> list[dict] | None:
    raw = redis_client.get(NOTIFICATIONS_CACHE_KEY.format(user_id=user_id))
    if raw is None:
        return None
    return json.loads(raw)


def set_cached_notifications(user_id: int, notifications: list[dict]) -> None:
    redis_client.set(
        NOTIFICATIONS_CACHE_KEY.format(user_id=user_id),
        json.dumps(notifications),
        ex=NOTIFICATIONS_CACHE_TTL_SECONDS,
    )


def invalidate_notifications_cache(user_id: int) -> None:
    redis_client.delete(NOTIFICATIONS_CACHE_KEY.format(user_id=user_id))
