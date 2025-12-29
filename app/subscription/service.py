from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.database.models import Subscription
from app.subscription.dto import CreateSubscriptionDto, UpdateSubscriptionDto
from app.subscription.repository import SubscriptionRepository
from app.user.service import UserService
from app.stripe.service import StripeService


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stripe_service = StripeService(session)
        self.subscription_repository = SubscriptionRepository(session)
        self.user_service = UserService(session)

    async def create_subscription(self, data: CreateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = Subscription(**data.model_dump())
        return await self.subscription_repository.create(subscription, commit=commit)

    async def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        return await self.subscription_repository.get_by_user_id(user_id)

    async def update_subscription(self, user_id: UUID, data: UpdateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = await self.subscription_repository.get_by_user_id(user_id)
        if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
        subscription.model_construct(**data.model_dump())
        return await self.subscription_repository.update(subscription.id, subscription, commit=commit)

    async def cancel_subscription(self, user_id: UUID, cancel_immediately: bool = False) -> Subscription:
        try:
            subscription = await self.subscription_repository.get_by_user_id(user_id)
            if not subscription or not subscription.stripe_subscription_id: raise HTTPException(status_code=404, detail="Subscription not found")
            stripe_subscription = await self.stripe_service.cancel_stripe_subscription(subscription.stripe_subscription_id, cancel_immediately)
            if not cancel_immediately: subscription.cancel_at_period_end = True
            subscription.status = stripe_subscription.status
            subscription.canceled_at = datetime.now(timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")

    async def update_subscription_plan(self, user_id: UUID, price_id: str) -> Subscription:
        try:
            subscription = await self.subscription_repository.get_by_user_id(user_id)
            if not subscription or not subscription.stripe_subscription_id: raise HTTPException(status_code=404, detail="Subscription not found")
            updated_stripe_sub = await self.stripe_service.update_stripe_subscription(subscription.stripe_subscription_id, price_id)
            plan = await self.stripe_service.get_plan_from_price_id(price_id)
            subscription.plan = plan
            subscription.stripe_price_id = price_id
            subscription.status = updated_stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(updated_stripe_sub.current_period_start, tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(updated_stripe_sub.current_period_end, tz=timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")

    async def sync_from_stripe(self, stripe_subscription_id: str) -> Subscription:
        try:
            stripe_sub = await self.stripe_service.retrieve_stripe_subscription(stripe_subscription_id)
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            subscription.status = stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc)
            subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
            if stripe_sub.canceled_at: subscription.canceled_at = datetime.fromtimestamp(stripe_sub.canceled_at, tz=timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to sync subscription: {str(e)}")
