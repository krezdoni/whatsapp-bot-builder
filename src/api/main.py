"""
EU Health AI Companion — FastAPI application entry point.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.database import engine, Base
from src.api.routes import auth, messaging, health_profile, documents, fhir, gdpr

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("starting", env=settings.app_env, llm=settings.llm_base_url)
    # Auto-create tables in dev (use Alembic migrations in production)
    if not settings.is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="EU Health AI Companion",
        description="GDPR-compliant personal health AI assistant for the European market.",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(messaging.router)
    app.include_router(health_profile.router)
    app.include_router(documents.router)
    app.include_router(fhir.router)
    app.include_router(gdpr.router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "eu-health-ai-companion"}

    return app


app = create_app()
