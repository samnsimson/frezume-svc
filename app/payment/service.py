import stripe
from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.config import settings
from app.database.models import User, Subscription, Plan
from app.payment.dto import CheckoutSessionDto, CreatePortalSessionDto
from app.payment.repository import PaymentRepository
from app.user.service import UserService
from app.subscription.service import SubscriptionService


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.payment_repository = PaymentRepository(session)
        self.user_service = UserService(session)
        self.subscription_service = SubscriptionService(session)
        stripe.api_key = settings.stripe_secret_key

    async def create_customer(self, user: User) -> str:
        try:
            customer = await stripe.Customer.create_async(email=user.email, name=user.name, metadata={"user_id": str(user.id)})
            subscription = await self.subscription_service.get_subscription(user.id)
            if not subscription: return customer.id
            updated_subscription = Subscription.model_construct(id=subscription.id, stripe_customer_id=customer.id)
            await self.payment_repository.update_subscription(updated_subscription, commit=False)
            return customer.id
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create Stripe customer: {str(e)}")

    async def get_or_create_customer(self, user: User) -> str:
        subscription = await self.subscription_service.get_subscription(user.id)
        if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
        if subscription.stripe_customer_id: return subscription.stripe_customer_id
        return await self.create_customer(user)

    async def create_subscription(self, user_id: UUID, price_id: str) -> Subscription:
        try:
            user = await self.user_service.get_user(user_id)
            customer_id = await self.get_or_create_customer(user)
            subscription = await stripe.Subscription.create_async(customer=customer_id, items=[{"price": price_id}], expand=["latest_invoice.payment_intent"])
            plan = await self._get_plan_from_price_id(price_id)
            db_subscription = Subscription(
                user_id=user_id,
                plan=plan,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription.id,
                stripe_price_id=price_id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
                cancel_at_period_end=subscription.cancel_at_period_end
            )
            return await self.payment_repository.create(db_subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")

    async def cancel_subscription(self, user_id: UUID, cancel_immediately: bool = False) -> Subscription:
        try:
            subscription = await self.payment_repository.get_by_user_id(user_id)
            if not subscription or not subscription.stripe_subscription_id: raise HTTPException(status_code=404, detail="Subscription not found")
            if cancel_immediately:
                await stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = "canceled"
                subscription.canceled_at = datetime.now(timezone.utc)
            else:
                await stripe.Subscription.modify_async(subscription.stripe_subscription_id, cancel_at_period_end=True)
                subscription.cancel_at_period_end = True
            return await self.payment_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")

    async def update_subscription(self, user_id: UUID, price_id: str) -> Subscription:
        try:
            user = await self.user_service.get_user(user_id)
            subscription = await self.payment_repository.get_by_user_id(user_id)
            if not subscription or not subscription.stripe_subscription_id: raise HTTPException(status_code=404, detail="Subscription not found")
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            stripe.Subscription.modify(subscription.stripe_subscription_id, items=[
                                       {"id": stripe_sub["items"]["data"][0].id, "price": price_id}], proration_behavior="always_invoice")
            plan = self._get_plan_from_price_id(price_id)
            subscription.plan = plan
            subscription.stripe_price_id = price_id
            updated_stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            subscription.status = updated_stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(updated_stripe_sub.current_period_start, tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(updated_stripe_sub.current_period_end, tz=timezone.utc)
            return await self.payment_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to update subscription: {str(e)}")

    async def get_subscription(self, user_id: UUID) -> Subscription | None:
        subscription = await self.payment_repository.get_by_user_id(user_id)
        if not subscription: return None
        return subscription

    async def create_checkout_session(self, dto: CheckoutSessionDto) -> str:
        try:
            user = await self.user_service.get_user(dto.user_id)
            customer_id = await self.get_or_create_customer(user)
            session = await stripe.checkout.Session.create_async(
                customer=customer_id,
                payment_method_types=["card", "paypal"],
                line_items=[{"price": dto.price_id, "quantity": 1}],
                mode="subscription",
                success_url=dto.success_url,
                cancel_url=dto.cancel_url,
                metadata={"user_id": str(dto.user_id)}
            )
            return session.url
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

    async def create_portal_session(self, dto: CreatePortalSessionDto) -> str:
        try:
            user = await self.user_service.get_user(dto.user_id)
            subscription = await self.subscription_service.get_subscription(dto.user_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            if not subscription.stripe_customer_id: raise HTTPException(status_code=400, detail="Subscription has no Stripe customer")
            session = await stripe.billing_portal.Session.create_async(customer=subscription.stripe_customer_id, return_url=dto.return_url)
            return session.url
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")

    async def _get_plan_from_price_id(self, price_id: str) -> Plan:
        price = await stripe.Price.retrieve_async(price_id)
        plan_name = price.metadata.get("plan", "free").lower()
        try: return Plan(plan_name)
        except ValueError: return Plan.FREE

    async def sync_subscription_from_stripe(self, stripe_subscription_id: str) -> Subscription:
        try:
            stripe_sub = await stripe.Subscription.retrieve_async(stripe_subscription_id)
            subscription = await self.payment_repository.get_by_stripe_subscription_id(stripe_subscription_id)
            if not subscription: raise HTTPException(status_code=404, detail="Subscription not found")
            subscription.status = stripe_sub.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc)
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc)
            subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
            if stripe_sub.canceled_at: subscription.canceled_at = datetime.fromtimestamp(stripe_sub.canceled_at, tz=timezone.utc)
            return await self.payment_repository.update_subscription(subscription, commit=False)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to sync subscription: {str(e)}")
