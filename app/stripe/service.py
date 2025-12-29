import stripe
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.config import settings
from app.database.models import User, Plan
from app.stripe.dto import CheckoutSessionDto
from app.user.service import UserService


class StripeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        stripe.api_key = settings.stripe_secret_key

    async def create_customer(self, user: User) -> stripe.Customer:
        try: return await stripe.Customer.create_async(email=user.email, name=user.name, metadata={"user_id": str(user.id)})
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create Stripe customer: {str(e)}")

    async def get_or_create_customer(self, user: User, subscription) -> str:
        if subscription and subscription.stripe_customer_id: return subscription.stripe_customer_id
        return await self.create_customer(user)

    async def create_checkout_session(self, dto: CheckoutSessionDto, subscription=None) -> str:
        try:
            user = await self.user_service.get_user(dto.user_id)
            customer_id = await self.get_or_create_customer(user, subscription)
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

    async def create_portal_session(self, stripe_customer_id: str, return_url: str) -> str:
        try: return await stripe.billing_portal.Session.create_async(customer=stripe_customer_id, return_url=return_url)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")

    async def get_plan_from_price_id(self, price_id: str) -> Plan:
        price = await stripe.Price.retrieve_async(price_id)
        plan_name = price.metadata.get("plan", "free").lower()
        try: return Plan(plan_name)
        except ValueError: return Plan.FREE

    async def create_stripe_subscription(self, customer_id: str, price_id: str) -> stripe.Subscription:
        try: return await stripe.Subscription.create_async(customer=customer_id, items=[{"price": price_id}], expand=["latest_invoice.payment_intent"])
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to create Stripe subscription: {str(e)}")

    async def cancel_stripe_subscription(self, stripe_subscription_id: str, cancel_immediately: bool = False) -> stripe.Subscription:
        try:
            if cancel_immediately: return await stripe.Subscription.cancel_async(stripe_subscription_id)
            else: return await stripe.Subscription.modify_async(stripe_subscription_id, cancel_at_period_end=True)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to cancel Stripe subscription: {str(e)}")

    async def update_stripe_subscription(self, stripe_subscription_id: str, price_id: str) -> stripe.Subscription:
        try:
            stripe_sub = await stripe.Subscription.retrieve_async(stripe_subscription_id)
            items = [{"id": stripe_sub["items"]["data"][0].id, "price": price_id}]
            await stripe.Subscription.modify_async(stripe_subscription_id, items=items, proration_behavior="always_invoice")
            return await stripe.Subscription.retrieve_async(stripe_subscription_id)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to update Stripe subscription: {str(e)}")

    async def retrieve_stripe_subscription(self, stripe_subscription_id: str) -> dict:
        try: return await stripe.Subscription.retrieve_async(stripe_subscription_id)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to retrieve Stripe subscription: {str(e)}")
