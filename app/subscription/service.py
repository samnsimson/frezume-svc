from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.database.models import Subscription
from app.subscription.dto import CreateSubscriptionDto, UpdateSubscriptionDto
from app.subscription.repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_repository = SubscriptionRepository(session)

    async def create_subscription(self, data: CreateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = Subscription(**data.model_dump())
        return await self.subscription_repository.create(subscription, commit=commit)

    async def get_subscription(self, user_id: UUID) -> Subscription:
        return await self.subscription_repository.get_by_user_id(user_id)

    async def update_subscription(self, user_id: UUID, data: UpdateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = await self.subscription_repository.get_by_user_id(user_id)
        if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
        subscription.model_construct(**data.model_dump())
        return await self.subscription_repository.update(subscription.id, subscription, commit=commit)
