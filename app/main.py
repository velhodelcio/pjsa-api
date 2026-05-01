from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import APIRouter, FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Startup / shutdown hooks quando precisar (BD, cache, etc.)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api.include_router(v1_router, prefix="/v1", tags=["v1"])
    app.include_router(api)

    return app


app = create_app()
