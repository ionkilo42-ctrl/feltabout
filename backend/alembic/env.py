"""Alembic environment — async SQLAlchemy"""
# type: ignore — alembic injects `context` and `op` as runtime globals
import asyncio
from logging.config import fileConfig

from alembic import context  # type: ignore
from sqlalchemy import pool  # type: ignore
from sqlalchemy.engine import Connection  # type: ignore
from sqlalchemy.ext.asyncio import async_engine_from_config  # type: ignore

import models  # noqa: F401 — needed for Base.metadata to be populated

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = models.Base.metadata


async def run_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
        await connection.commit()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if asyncio.get_event_loop().is_running():
    asyncio.create_task(run_migrations())
else:
    asyncio.run(run_migrations())
