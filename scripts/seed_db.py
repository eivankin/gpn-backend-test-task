import asyncio
from pathlib import Path

from advanced_alchemy.base import BigIntAuditBase
from advanced_alchemy.config import AsyncSessionConfig, SQLAlchemyAsyncConfig
from advanced_alchemy.exceptions import DuplicateKeyError
from advanced_alchemy.utils.fixtures import open_fixture_async
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine

from app import models
from app.repositories import UsersRepository
from app.settings import settings


alchemy_config = SQLAlchemyAsyncConfig(
    engine_instance=create_async_engine(settings.db_dsn_parsed),
    session_config=AsyncSessionConfig(expire_on_commit=False),
)

fixtures_path = Path(__file__).parent / "fixtures"


async def initialize_database() -> None:
    async with alchemy_config.get_engine().begin() as conn:
        await conn.run_sync(BigIntAuditBase.metadata.create_all)


async def seed_database() -> None:
    # Create a session
    async with alchemy_config.get_session() as db_session:
        # Create repository for user model
        users_repo = UsersRepository(session=db_session)

        # Load and add user
        saved_users = []
        try:
            user_data = await open_fixture_async(fixtures_path, "users")
            saved_users = await users_repo.add_many([models.User(**item) for item in user_data])
            await db_session.commit()
            logger.info("Users seeded successfully")
        except FileNotFoundError:
            logger.error("User fixtures not found")
        except DuplicateKeyError:
            logger.warning("Users already seeded")

        if saved_users:
            try:
                # Load and add note
                note_data = await open_fixture_async(fixtures_path, "notes")
                await users_repo.add_many(
                    [models.Note(**item, author_id=user.id) for item, user in zip(note_data, saved_users, strict=False)]
                )
                await db_session.commit()
                logger.info("Notes seeded successfully")
            except FileNotFoundError:
                logger.error("Note fixtures not found")


async def main() -> None:
    # Initialize the database
    await initialize_database()

    # Seed the database
    await seed_database()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
