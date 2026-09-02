import redis
import sqlalchemy
from confluent_kafka.admin import AdminClient
from fastapi import APIRouter
from sqlalchemy import create_engine, text

from app.core.config import settings

router = APIRouter()


def _check_postgres() -> str:
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except sqlalchemy.exc.SQLAlchemyError as exc:
        return f"unreachable: {exc.__class__.__name__}"


def _check_redis() -> str:
    try:
        client = redis.Redis(
            host=settings.redis_host, port=settings.redis_port, socket_connect_timeout=2
        )
        client.ping()
        return "ok"
    except redis.RedisError as exc:
        return f"unreachable: {exc.__class__.__name__}"


def _check_kafka() -> str:
    try:
        admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})
        cluster_metadata = admin.list_topics(timeout=2)
        if cluster_metadata.brokers:
            return "ok"
        return "unreachable: no brokers reported"
    except Exception as exc:  # confluent-kafka raises its own KafkaException
        return f"unreachable: {exc.__class__.__name__}"


@router.get("/health")
def health_check():
    checks = {
        "postgres": _check_postgres(),
        "redis": _check_redis(),
        "kafka": _check_kafka(),
    }
    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
