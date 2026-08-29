from typing import AsyncGenerator
from fastapi import Request, Depends
import asyncpg

# retrieves the database pool for retrieval of connection
def get_db_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool

async def get_connection(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> AsyncGenerator[asyncpg.Connection, None]:
    async with pool.acquire() as conn:
        yield conn
