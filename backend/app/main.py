from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.database import Base, engine
from app.routers import auth, safety, subscription, takes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(safety.router)
app.include_router(takes.router)
app.include_router(subscription.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/v1/lenses")
async def list_lenses():
    """Return all 20 lens definitions (metadata only, no system prompts)."""
    from app.lenses.definitions import get_all_lenses

    return [
        {
            "index": l["index"],
            "name": l["name"],
            "emoji": l["emoji"],
            "color": l["color"],
            "bg": l["bg"],
        }
        for l in get_all_lenses()
    ]
