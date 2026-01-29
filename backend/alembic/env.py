"""
Alembic Environment Configuration
===================================

Configures Alembic migrations to work with:
- Async SQLAlchemy engine
- Our database models for autogenerate support
- Database URL from config.py
"""

import asyncio
import ssl
from logging.config import fileConfig
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from alembic import context

# Import our models and config
from config import settings
from models.database import Base
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from config.py (overrides alembic.ini)
# Convert to async URL for asyncpg
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# asyncpg doesn't understand sslmode query param - strip it and all other
# non-asyncpg params, then pass SSL via connect_args instead
connect_args = {}
if database_url:
    parsed = urlsplit(database_url)
    query_params = parse_qs(parsed.query)
    # Remove params that asyncpg doesn't understand
    needs_ssl = False
    for param in ["sslmode", "channel_binding"]:
        if param in query_params:
            query_params.pop(param)
            needs_ssl = True
    new_query = urlencode(query_params, doseq=True)
    database_url = urlunsplit(parsed._replace(query=new_query))
    if needs_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    Creates an async Engine and acquires a connection from it.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
