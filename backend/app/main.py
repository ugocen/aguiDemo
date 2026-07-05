from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, agui_router, conversations
from app.config.settings import get_settings
from app.db.session import create_all, dispose_engine, init_engine
from app.logging.setup import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_engine(settings)
    try:
        await create_all()
        log.info("db_ready")
    except Exception as exc:  # noqa: BLE001
        log.warning("db_unavailable", error=str(exc))
    yield
    await dispose_engine()


app = FastAPI(title="AG-UI Demo Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agui_router.router)
app.include_router(conversations.router)
app.include_router(agents.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "agent_mode": settings.agent_mode, "auth_mode": settings.auth_mode}
