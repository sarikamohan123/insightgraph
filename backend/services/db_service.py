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

# asyncpg doesn't understand sslmode query param - strip it and use connect_args instead
import ssl
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

connect_args = {}
if database_url:
    parsed = urlsplit(database_url)
    query_params = parse_qs(parsed.query)
    if "sslmode" in query_params:
        query_params.pop("sslmode")
        query_params.pop("channel_binding", None)
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunsplit(parsed._replace(query=new_query))
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

engine = create_async_engine(
    database_url,
    echo=False,  # Set to True for SQL query logging (useful for debugging)
    pool_size=5,  # Reduced for serverless (Neon free tier has limits)
    max_overflow=10,  # Max connections beyond pool_size
    pool_pre_ping=True,  # Check if connection is alive before using (fixes stale connections)
    pool_recycle=300,  # Recycle connections every 5 minutes (Neon can close idle connections)
    connect_args=connect_args,
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
                print(
                    "[Database] WARNING: Tables not found. Run 'alembic upgrade head' to create schema."
                )
                return False

            return True

    except Exception as e:
        print(f"[Database] ERROR: Connection failed - {e}")
        raise


async def close_db():
    """Close database connections."""
    await engine.dispose()
    print("[Database] Connections closed")
