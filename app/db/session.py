"""Async database engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.db.base import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine_url(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return settings.database_url


def init_engine(settings: Settings | None = None) -> None:
    """Create global async engine and session factory."""
    global _engine, _session_factory
    settings = settings or get_settings()
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.app_env == "local" and settings.log_level.upper() == "DEBUG",
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables(engine_url: str | None = None) -> None:
    """Create tables (tests / sqlite). Prefer Alembic in production."""
    from sqlalchemy.ext.asyncio import create_async_engine

    url = engine_url or get_engine_url()
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
