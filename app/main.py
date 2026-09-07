from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.simulate import router as simulate_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(simulate_router)
