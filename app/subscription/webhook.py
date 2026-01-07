from fastapi import Request, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import settings
from app.subscription.service import SubscriptionService
from app.lib.constants import (
    ERROR_INVALID_PAYLOAD,
    ERROR_INVALID_SIGNATURE,
)
from uuid import UUID
import stripe


async def handle_stripe_webhook(request: Request, session: AsyncSession):
    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try: event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError: raise HTTPException(status_code=400, detail=ERROR_INVALID_PAYLOAD)
    except stripe.error.SignatureVerificationError: raise HTTPException(status_code=400, detail=ERROR_INVALID_SIGNATURE)

    subscription_service = SubscriptionService(session)
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        checkout_session = event["data"]["object"]
        if checkout_session.get("mode") == "subscription":
            user_id = checkout_session.get("metadata", {}).get("user_id")
            subscription_id = checkout_session.get("subscription")
            if user_id and subscription_id: await subscription_service.link_stripe_subscription(UUID(user_id), subscription_id)

    elif event_type == "customer.subscription.created":
        stripe_subscription = event["data"]["object"]
        customer_id = stripe_subscription.get("customer")
        subscription_id = stripe_subscription.get("id")
        if customer_id and subscription_id:
            subscription = await subscription_service.get_by_stripe_customer_id(customer_id)
            if subscription: await subscription_service.link_stripe_subscription(subscription.user_id, subscription_id)

    elif event_type == "customer.subscription.updated" or event_type == "customer.subscription.deleted":
        subscription_id = event["data"]["object"]["id"]
        await subscription_service.sync_from_stripe(subscription_id)

    return {"status": "success"}
