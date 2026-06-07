from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Import all models so Base.metadata is complete before engine creation
import app.models  # noqa: F401
from app.db.base import Base

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Async engine & session factory (module-level globals)
# ---------------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # SQLite does not support RETURNING clause
    implicit_returning=False,
)

# Fix SQLite BIGINT autoincrement: override BigInteger type for SQLite compatibility
if "sqlite" in settings.DATABASE_URL:
    from sqlalchemy import Integer
    from sqlalchemy.dialects.sqlite.base import SQLiteDialect

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    # Make all BigInteger columns use INTEGER for SQLite compatibility
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.type.__class__.__name__ == "BigInteger":
                col.type = Integer()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup and dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created.")
    yield
    await engine.dispose()
    logger.info("Database engine disposed.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME + " API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Routers (each router defines its own prefix)
# ---------------------------------------------------------------------------

from app.api import auth, job_records, sources, tasks, templates, workspaces, ai  # noqa: E402, F401

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(templates.router)
app.include_router(tasks.router)
app.include_router(job_records.router)
app.include_router(sources.router)
app.include_router(ai.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.PROJECT_NAME}
