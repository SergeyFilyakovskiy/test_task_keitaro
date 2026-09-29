from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import async_session
from app.infrastructure.external.keitaro_client import KeitaroClient


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.aclose()


def get_keitaro() -> KeitaroClient:
    return KeitaroClient()
