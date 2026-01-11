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

import sqlalchemy as sa
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


async def check_db_connection():
    """
    Check database connectivity.

    Verifies that the database is reachable and tables exist.
    Does NOT create or modify schema - use Alembic migrations for that.

    Returns:
        bool: True if connected and tables exist, False otherwise

    Raises:
        Exception: If database is unreachable
    """
    try:
        async with engine.connect() as conn:
            # Test basic connectivity
            await conn.execute(sa.text("SELECT 1"))

            # Check if graphs table exists (indicating migrations were run)
            result = await conn.execute(
                sa.text(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'graphs'
                    )
                    """
                )
            )
            tables_exist = result.scalar()

            if not tables_exist:
                print("[Database] WARNING: Tables not found. Run 'alembic upgrade head' to create schema.")
                return False

            return True

    except Exception as e:
        print(f"[Database] ERROR: Connection failed - {e}")
        raise


async def close_db():
    """Close database connections."""
    await engine.dispose()
    print("[Database] Connections closed")
