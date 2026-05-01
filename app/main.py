import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.seed import seed_admin_if_configured
from app.database import AsyncSessionLocal, Base, engine
from app.api.routers import auth, dashboard, orders, products

logger = logging.getLogger(__name__)


async def _create_all_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    import app.models  # noqa: F401 — regista tabelas no metadata

    delays = (0, 1, 2, 3, 5, 5, 5)
    last_exc: BaseException | None = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            await asyncio.sleep(delay)
        try:
            await _create_all_schema()
            last_exc = None
            break
        except (OSError, OperationalError) as exc:
            last_exc = exc
            logger.warning(
                "Base de dados indisponível (tentativa %s/%s): %s",
                attempt,
                len(delays),
                exc,
            )
    if last_exc is not None:
        raise RuntimeError(
            "Não foi possível ligar à base de dados após várias tentativas. "
            "Confirma que DATABASE_URL está correto (no Docker o host é 'postgres' e a porta interna 5432)."
        ) from last_exc

    async with AsyncSessionLocal() as session:
        await seed_admin_if_configured(session)
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

    api.include_router(products.router, tags=["products"])
    api.include_router(orders.router, tags=["orders"])
    api.include_router(auth.router, prefix="/auth", tags=["auth"])
    api.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(api)

    return app


app = create_app()
