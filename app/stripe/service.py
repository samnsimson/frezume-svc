import stripe
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from app.config import settings
from app.database.models import Plan
from app.lib.constants import (
    ERROR_FAILED_TO_CREATE_STRIPE_CUSTOMER,
    ERROR_FAILED_TO_CREATE_CHECKOUT_SESSION,
    ERROR_FAILED_TO_CREATE_PORTAL_SESSION,
    ERROR_FAILED_TO_CREATE_STRIPE_SUBSCRIPTION,
    ERROR_FAILED_TO_CANCEL_STRIPE_SUBSCRIPTION,
    ERROR_FAILED_TO_UPDATE_STRIPE_SUBSCRIPTION,
    ERROR_FAILED_TO_RETRIEVE_STRIPE_SUBSCRIPTION,
)


class StripeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        stripe.api_key = settings.stripe_secret_key

    async def create_customer(self, email: str, name: str, user_id: str) -> stripe.Customer:
        try: return await stripe.Customer.create_async(email=email, name=name, metadata={"user_id": user_id})
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_STRIPE_CUSTOMER.format(error=str(e)))

    def _build_checkout_params(self, customer_id: str, price_id: str, success_url: str, cancel_url: str, user_id: str) -> dict:
        return {
            "customer": customer_id,
            "payment_method_types": ["card", "paypal"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {"user_id": user_id}
        }

    async def create_checkout_session(self, customer_id: str, price_id: str, success_url: str, cancel_url: str, user_id: str) -> str:
        try:
            checkout_params = self._build_checkout_params(customer_id, price_id, success_url, cancel_url, user_id)
            session = await stripe.checkout.Session.create_async(**checkout_params)
            return session.url
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_CHECKOUT_SESSION.format(error=str(e)))

    async def create_portal_session(self, stripe_customer_id: str, return_url: str) -> str:
        try: return (await stripe.billing_portal.Session.create_async(customer=stripe_customer_id, return_url=return_url)).url
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_PORTAL_SESSION.format(error=str(e)))

    def _extract_plan_name(self, price: dict) -> str:
        return price.metadata.get("plan", "free").lower()

    async def get_plan_from_price_id(self, price_id: str) -> Plan:
        price = await stripe.Price.retrieve_async(price_id)
        try: return Plan(self._extract_plan_name(price))
        except ValueError: return Plan.FREE

    async def create_stripe_subscription(self, customer_id: str, price_id: str) -> stripe.Subscription:
        try: return await stripe.Subscription.create_async(customer=customer_id, items=[{"price": price_id}], expand=["latest_invoice.payment_intent"])
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CREATE_STRIPE_SUBSCRIPTION.format(error=str(e)))

    async def cancel_stripe_subscription(self, stripe_subscription_id: str, cancel_immediately: bool = False) -> dict:
        try:
            if cancel_immediately: return await stripe.Subscription.cancel_async(stripe_subscription_id)
            return await stripe.Subscription.modify_async(stripe_subscription_id, cancel_at_period_end=True)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_CANCEL_STRIPE_SUBSCRIPTION.format(error=str(e)))

    def _build_subscription_items(self, stripe_sub: dict, price_id: str) -> list:
        return [{"id": stripe_sub["items"]["data"][0]["id"], "price": price_id}]

    async def update_stripe_subscription(self, stripe_subscription_id: str, price_id: str) -> dict:
        try:
            stripe_sub = await stripe.Subscription.retrieve_async(stripe_subscription_id)
            await stripe.Subscription.modify_async(stripe_subscription_id, items=self._build_subscription_items(stripe_sub, price_id), proration_behavior="always_invoice")
            return await stripe.Subscription.retrieve_async(stripe_subscription_id)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_UPDATE_STRIPE_SUBSCRIPTION.format(error=str(e)))

    async def retrieve_stripe_subscription(self, stripe_subscription_id: str) -> dict:
        try: return await stripe.Subscription.retrieve_async(stripe_subscription_id)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_RETRIEVE_STRIPE_SUBSCRIPTION.format(error=str(e)))
