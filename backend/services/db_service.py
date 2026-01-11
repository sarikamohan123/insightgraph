"""
Database Service - Connection Management
==========================================

Handles async database connections and session management using SQLAlchemy.

Architecture:
- Async engine for non-blocking I/O
- Session factory for request-scoped transactions
- Context manager for automatic session cleanup

Usage:
    async with get_db_session() as session:
        result = await session.execute(select(Graph))
        graphs = result.scalars().all()
"""

from contextlib import asynccontextmanager

from config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Create async engine
# Convert sync postgres:// URL to async postgresql+asyncpg://
database_url = settings.database_url
if database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL query logging (useful for debugging)
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max connections beyond pool_size
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
)


@asynccontextmanager
async def get_db_session():
    """
    Get async database session.

    Usage:
        async with get_db_session() as session:
            # Use session here
            result = await session.execute(query)

    Session is automatically closed when context manager exits.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database (create tables if they don't exist).

    NOTE: In production, use Alembic migrations instead.
    This is mainly for development and testing.
    """
    from models.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[Database] Tables created successfully")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    print("[Database] Connections closed")
