from fastapi import Request, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import settings
from app.payment.service import PaymentService
import stripe


async def handle_stripe_webhook(request: Request, session: AsyncSession):
    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try: event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError: raise HTTPException(status_code=400, detail="Invalid signature")

    stripe_service = PaymentService(session)
    if event["type"] == "customer.subscription.updated" or event["type"] == "customer.subscription.deleted":
        subscription_id = event["data"]["object"]["id"]
        await stripe_service.sync_subscription_from_stripe(subscription_id)
    return {"status": "success"}
