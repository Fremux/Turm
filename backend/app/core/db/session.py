from contextlib import contextmanager
from typing import AsyncGenerator

from settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


async_engine = create_async_engine(
    "{}://{}:{}@{}:{}/{}".format(
        "postgresql+asyncpg",
        settings.POSTGRES_USER,
        settings.POSTGRES_PASSWORD,
        settings.DB_ADDR,
        settings.DB_PORT,
        settings.POSTGRES_DB,
    )
)

async_session_maker = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, expire_on_commit=False
)


async def get_async_database() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@contextmanager
async def with_database():
    db: AsyncSession = async_session_maker()

    try:
        yield db
        await db.commit()
    except:
        await db.rollback()
        raise
