from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.database.models import Subscription, Plan
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

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Subscription | None:
        return await self.subscription_repository.get_by_stripe_customer_id(stripe_customer_id)

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
            subscription.status = stripe_subscription['status']
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
            subscription.status = updated_stripe_sub["status"]
            subscription.current_period_start = datetime.fromtimestamp(updated_stripe_sub["current_period_start"], tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(updated_stripe_sub["current_period_end"], tz=timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")

    async def link_stripe_subscription(self, user_id: UUID, stripe_subscription_id: str) -> Subscription:
        try:
            stripe_sub = await self.stripe_service.retrieve_stripe_subscription(stripe_subscription_id)
            subscription = await self.subscription_repository.get_by_user_id(user_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            price_id = stripe_sub["items"]["data"][0]["price"]["id"]
            plan = await self.stripe_service.get_plan_from_price_id(price_id)
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.stripe_price_id = price_id
            subscription.plan = plan
            subscription.status = stripe_sub["status"]
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"], tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"], tz=timezone.utc)
            subscription.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
            if stripe_sub.get("canceled_at"): subscription.canceled_at = datetime.fromtimestamp(stripe_sub["canceled_at"], tz=timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to link Stripe subscription: {str(e)}")

    async def sync_from_stripe(self, stripe_subscription_id: str) -> Subscription:
        try:
            stripe_sub = await self.stripe_service.retrieve_stripe_subscription(stripe_subscription_id)
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            subscription.status = stripe_sub["status"]
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"], tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"], tz=timezone.utc)
            subscription.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
            if stripe_sub.get("canceled_at"): subscription.canceled_at = datetime.fromtimestamp(stripe_sub["canceled_at"], tz=timezone.utc)
            return await self.subscription_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to sync subscription: {str(e)}")

    async def create_checkout_session(self, user_id: UUID, price_id: str, success_url: str, cancel_url: str) -> str:
        try:
            user = await self.user_service.get_user(user_id)
            subscription = await self.get_by_user_id(user_id)
            customer_id = subscription.stripe_customer_id if subscription and subscription.stripe_customer_id else None
            if not customer_id:
                customer = await self.stripe_service.create_customer(user.email, user.name, str(user.id))
                customer_id = customer.id
                if subscription:
                    subscription.stripe_customer_id = customer_id
                    await self.subscription_repository.update_subscription(subscription, commit=False)
            return await self.stripe_service.create_checkout_session(customer_id, price_id, success_url, cancel_url, str(user_id))
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

    async def create_portal_session(self, user_id: UUID, return_url: str) -> str:
        try:
            subscription = await self.get_by_user_id(user_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            if not subscription.stripe_customer_id: raise HTTPException(status_code=400, detail="Subscription has no Stripe customer")
            return await self.stripe_service.create_portal_session(subscription.stripe_customer_id, return_url)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")
