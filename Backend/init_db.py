import asyncio
import os
import asyncpg

from app.auth.auth import hash_password, insert_user
from app.core.env import Postgres_Settings

async def seed_users(connection: asyncpg.Connection):
    admin_user = os.getenv("ADMIN_NAME", "")
    admin_email = os.getenv("ADMIN_EMAIL", "")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")

    if admin_email != "" and admin_pass != "" and admin_user != "":
        admin_pass = hash_password(admin_pass)
        await insert_user(email=admin_email, username=admin_user, role="ADMIN", hashed_password=admin_pass, connection=connection)
    else:
        print("A needed environment variable is missing from the .env for admin")


    if os.getenv("ENVIRONMENT", "") == "development":
        user_user = os.getenv("E2E_USER_NAME", "")
        user_email = os.getenv("E2E_USER_EMAIL", "")
        user_pass = os.getenv("E2E_USER_PASSWORD", "")

        if user_email != "" and user_pass != "" and user_user != "":
            user_pass = hash_password(user_pass)
            await insert_user(email=user_email, username=user_user, role="USER", hashed_password=user_pass, connection=connection)
        else:
            print("A needed environment variable is missing from the .env for the user")

        invest_user = os.getenv("E2E_INVESTIGATOR_NAME", "")
        invest_email = os.getenv("E2E_INVESTIGATOR_EMAIL", "")
        invest_pass = os.getenv("E2E_INVESTIGATOR_PASSWORD", "")

        if invest_email != "" and invest_pass != "" and invest_user != "":
            invest_pass = hash_password(invest_pass)
            await insert_user(email=invest_email, username=invest_user, role="INVESTIGATOR", hashed_password=invest_pass, connection=connection)
        else:
            print("A needed environment variable is missing from the .env for the investigator")

if __name__ == "__main__":
    settings = Postgres_Settings()

    async def initialize_users():
        pool = await asyncpg.create_pool(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            ssl="require" if settings.DB_SSL else None,
        )
        try:
            async with pool.acquire() as connection:
                await seed_users(connection)
        finally:
            await pool.close()

    asyncio.run(initialize_users())