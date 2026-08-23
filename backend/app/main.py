import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import get_redis
from app.services.watchdog import run_watchdog
from app.ws import routes as ws_routes
from app.ws.eventbus import start_reader

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_redis()
    reader_task = asyncio.create_task(start_reader())
    watchdog_task = asyncio.create_task(run_watchdog())
    yield
    watchdog_task.cancel()
    reader_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Pear Energy API — управление зарядными станциями",
    openapi_tags=[
        {"name": "auth"}, {"name": "me"}, {"name": "stations"}, {"name": "charging"},
        {"name": "payments"}, {"name": "bookings"}, {"name": "support"},
        {"name": "operator"}, {"name": "admin"},
    ],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_routes.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
