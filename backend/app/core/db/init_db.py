import models

from core.db.session import async_engine


async def init_database() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(models.base.Base.metadata.create_all)
