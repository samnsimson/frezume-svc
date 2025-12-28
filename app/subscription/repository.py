from uuid import UUID
from app.database.models import Subscription
from app.database.repository import Repository
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class SubscriptionRepository(Repository[Subscription]):
    def __init__(self, session: AsyncSession):
        super().__init__(Subscription, session)

    async def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()
