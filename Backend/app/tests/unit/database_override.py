import inspect
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import asyncpg
from fastapi import Request

from app.api.routers import cases_router

ORIGINAL_ASYNCPG_CONNECT = asyncpg.connect


async def unit_get_connection(request: Request) -> AsyncGenerator[AsyncMock, None]:
    connect_fn = getattr(cases_router.asyncpg, "connect", ORIGINAL_ASYNCPG_CONNECT)
    connection = AsyncMock()

    if callable(connect_fn) and connect_fn is not ORIGINAL_ASYNCPG_CONNECT:
        result = connect_fn()
        if inspect.isawaitable(result):
            result = await result
        if result is not None:
            connection = result

    try:
        yield connection
    finally:
        close_method = getattr(connection, "close", None)
        if callable(close_method):
            close_result = close_method()
            if inspect.isawaitable(close_result):
                await close_result