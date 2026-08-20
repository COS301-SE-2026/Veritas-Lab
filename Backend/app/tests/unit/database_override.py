import inspect
from collections.abc import AsyncGenerator

import asyncpg
from fastapi import Request

from app.api.routers import cases_router
from app.core.database import get_connection as database_get_connection
from app.core.env import Postgres_Settings


postgres_settings = Postgres_Settings()


async def unit_get_connection(request: Request) -> AsyncGenerator[asyncpg.Connection, None]:
    patched_dependency = cases_router.get_connection

    if patched_dependency is not database_get_connection:
        connection = patched_dependency()
        if inspect.isawaitable(connection):
            connection = await connection
        elif inspect.isasyncgen(connection):
            connection = await anext(connection)
    else:
        connection = await asyncpg.connect(
            user=postgres_settings.DB_USER,
            password=postgres_settings.DB_PASSWORD,
            database=postgres_settings.DB_NAME,
            host=postgres_settings.DB_HOST,
            port=postgres_settings.DB_PORT,
            ssl="require" if postgres_settings.DB_SSL else None,
        )

    try:
        yield connection
    finally:
        if connection is not None:
            await connection.close()