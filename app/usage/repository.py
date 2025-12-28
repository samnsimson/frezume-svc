from uuid import UUID
from app.database.repository import Repository
from app.database.models import Usage
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class UsageRepository(Repository[Usage]):
    def __init__(self, session: AsyncSession):
        super().__init__(Usage, session)

    async def get_by_user_id(self, user_id: UUID) -> Usage | None:
        stmt = select(Usage).where(Usage.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()
