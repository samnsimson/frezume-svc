from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.database.models import Subscription, User
from app.subscription.dto import CreateSubscriptionDto, UpdateSubscriptionDto
from app.subscription.repository import SubscriptionRepository
from app.stripe.service import StripeService
from app.lib.constants import (
    ERROR_SUBSCRIPTION_NOT_FOUND,
    ERROR_SUBSCRIPTION_NO_STRIPE_CUSTOMER,
    ERROR_FAILED_TO_CANCEL_SUBSCRIPTION,
    ERROR_FAILED_TO_UPDATE_SUBSCRIPTION,
    ERROR_FAILED_TO_LINK_STRIPE_SUBSCRIPTION,
    ERROR_FAILED_TO_SYNC_SUBSCRIPTION,
    ERROR_FAILED_TO_CREATE_CHECKOUT_SESSION,
    ERROR_FAILED_TO_CREATE_PORTAL_SESSION,
)


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stripe_service = StripeService(session)
        self.subscription_repository = SubscriptionRepository(session)

    async def create_subscription(self, data: CreateSubscriptionDto, commit: bool = False) -> Subscription:
        return await self.subscription_repository.create(Subscription(**data.model_dump()), commit=commit)

    async def get_by_user_id(self, user_id: UUID) -> Subscription | None:
        return await self.subscription_repository.get_by_user_id(user_id)

    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Subscription | None:
        return await self.subscription_repository.get_by_stripe_customer_id(stripe_customer_id)

    async def update_subscription(self, user_id: UUID, data: UpdateSubscriptionDto, commit: bool = False) -> Subscription:
        subscription = await self._get_subscription_by_user(user_id)
        subscription.model_construct(**data.model_dump())
        return await self.subscription_repository.update(subscription.id, subscription, commit=commit)

    async def cancel_subscription(self, user_id: UUID, cancel_immediately: bool = False) -> Subscription:
        try:
            subscription = await self._get_subscription_with_stripe_id(user_id)
            stripe_sub = await self.stripe_service.cancel_stripe_subscription(subscription.stripe_subscription_id, cancel_immediately)
            if not cancel_immediately: subscription.cancel_at_period_end = True
            subscription.status = stripe_sub['status']
            subscription.canceled_at = datetime.now(timezone.utc)
            return await self._save_subscription(subscription)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CANCEL_SUBSCRIPTION.format(error=str(e)))

    async def update_subscription_plan(self, user_id: UUID, price_id: str) -> Subscription:
        try:
            subscription = await self._get_subscription_with_stripe_id(user_id)
            stripe_sub = await self.stripe_service.update_stripe_subscription(subscription.stripe_subscription_id, price_id)
            plan = await self.stripe_service.get_plan_from_price_id(price_id)
            subscription.plan = plan
            subscription.stripe_price_id = price_id
            self._update_periods(subscription, stripe_sub)
            return await self._save_subscription(subscription)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_UPDATE_SUBSCRIPTION.format(error=str(e)))

    async def link_stripe_subscription(self, user_id: UUID, stripe_subscription_id: str) -> Subscription:
        try:
            subscription = await self._get_subscription_by_user(user_id)
            stripe_sub = await self.stripe_service.retrieve_stripe_subscription(stripe_subscription_id)
            price_id = self._extract_price_id(stripe_sub)
            plan = await self.stripe_service.get_plan_from_price_id(price_id)
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.stripe_price_id = price_id
            subscription.plan = plan
            self._update_from_stripe(subscription, stripe_sub)
            return await self._save_subscription(subscription)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_LINK_STRIPE_SUBSCRIPTION.format(error=str(e)))

    async def sync_from_stripe(self, stripe_subscription_id: str) -> Subscription:
        try:
            subscription = await self.subscription_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if not subscription: raise HTTPException(status_code=404, detail=ERROR_SUBSCRIPTION_NOT_FOUND)
            stripe_sub = await self.stripe_service.retrieve_stripe_subscription(stripe_subscription_id)
            self._update_from_stripe(subscription, stripe_sub)
            return await self._save_subscription(subscription)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_SYNC_SUBSCRIPTION.format(error=str(e)))

    async def create_checkout_session(self, user: User, price_id: str, success_url: str, cancel_url: str) -> str:
        try:
            subscription = await self.get_by_user_id(user.id)
            customer_id = await self._get_or_create_customer(user, subscription)
            return await self.stripe_service.create_checkout_session(customer_id, price_id, success_url, cancel_url, str(user.id))
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_CHECKOUT_SESSION.format(error=str(e)))

    async def create_portal_session(self, user: User, return_url: str) -> str:
        try:
            subscription = await self.get_by_user_id(user.id)
            if not subscription: raise HTTPException(status_code=404, detail=ERROR_SUBSCRIPTION_NOT_FOUND)
            if not subscription.stripe_customer_id: raise HTTPException(status_code=400, detail=ERROR_SUBSCRIPTION_NO_STRIPE_CUSTOMER)
            return await self.stripe_service.create_portal_session(subscription.stripe_customer_id, return_url)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_PORTAL_SESSION.format(error=str(e)))

    async def _get_subscription_by_user(self, user_id: UUID) -> Subscription:
        subscription = await self.subscription_repository.get_by_user_id(user_id)
        if not subscription: raise HTTPException(status_code=404, detail=ERROR_SUBSCRIPTION_NOT_FOUND)
        return subscription

    async def _get_subscription_with_stripe_id(self, user_id: UUID) -> Subscription:
        subscription = await self._get_subscription_by_user(user_id)
        if not subscription.stripe_subscription_id: raise HTTPException(status_code=404, detail=ERROR_SUBSCRIPTION_NOT_FOUND)
        return subscription

    async def _get_or_create_customer(self, user: User, subscription: Subscription | None) -> str:
        if subscription and subscription.stripe_customer_id: return subscription.stripe_customer_id
        customer = await self.stripe_service.create_customer(user.email, user.name, str(user.id))
        if subscription:
            subscription.stripe_customer_id = customer.id
            await self._save_subscription(subscription)
        return customer.id

    def _update_from_stripe(self, subscription: Subscription, stripe_sub: dict) -> None:
        subscription.status = stripe_sub["status"]
        self._update_periods(subscription, stripe_sub)
        subscription.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)
        if stripe_sub.get("canceled_at"): subscription.canceled_at = datetime.fromtimestamp(stripe_sub["canceled_at"], tz=timezone.utc)

    def _update_periods(self, subscription: Subscription, stripe_sub: dict) -> None:
        subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"], tz=timezone.utc)
        subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"], tz=timezone.utc)

    def _extract_price_id(self, stripe_sub: dict) -> str:
        return stripe_sub["items"]["data"][0]["price"]["id"]

    async def _save_subscription(self, subscription: Subscription) -> Subscription:
        return await self.subscription_repository.update_subscription(subscription, commit=False)
