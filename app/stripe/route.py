from fastapi import APIRouter, Request, HTTPException
from app.stripe.dto import (
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    CreatePortalSessionRequest,
    CreatePortalSessionResponse,
    UpdateSubscriptionRequest,
    CancelSubscriptionRequest,
    SubscriptionResponse
)
from app.stripe.service import StripeService
from app.lib.dependency import DatabaseSession, AuthSession
from app.lib.context.transaction import transactional

router = APIRouter(tags=["stripe"])


@router.post("/checkout", operation_id="createCheckoutSession", response_model=CreateCheckoutSessionResponse)
def create_checkout_session(data: CreateCheckoutSessionRequest, session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        url = stripe_service.create_checkout_session(user_session.user.id, data.price_id, data.success_url, data.cancel_url)
        return CreateCheckoutSessionResponse(url=url)


@router.post("/portal", operation_id="createPortalSession", response_model=CreatePortalSessionResponse)
def create_portal_session(data: CreatePortalSessionRequest, session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        url = stripe_service.create_portal_session(user_session.user.id, data.return_url)
        return CreatePortalSessionResponse(url=url)


@router.get("/subscription", operation_id="getSubscription", response_model=SubscriptionResponse)
def get_subscription(session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        subscription = stripe_service.get_subscription(user_session.user.id)
        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan=subscription.plan,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_price_id=subscription.stripe_price_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )


@router.put("/subscription", operation_id="updateSubscription", response_model=SubscriptionResponse)
def update_subscription(data: UpdateSubscriptionRequest, session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        subscription = stripe_service.update_subscription(user_session.user.id, data.price_id)
        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan=subscription.plan,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_price_id=subscription.stripe_price_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )


@router.post("/subscription/cancel", operation_id="cancelSubscription", response_model=SubscriptionResponse)
def cancel_subscription(data: CancelSubscriptionRequest, session: DatabaseSession, user_session: AuthSession):
    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        subscription = stripe_service.cancel_subscription(user_session.user.id, data.cancel_immediately)
        return SubscriptionResponse(
            id=str(subscription.id),
            user_id=str(subscription.user_id),
            plan=subscription.plan,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_price_id=subscription.stripe_price_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )


@router.post("/webhook", operation_id="stripeWebhook")
async def stripe_webhook(request: Request, session: DatabaseSession):
    from app.config import settings
    import stripe
    import json

    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except ValueError: raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError: raise HTTPException(status_code=400, detail="Invalid signature")

    with transactional(session) as ses:
        stripe_service = StripeService(ses)
        if event["type"] == "customer.subscription.updated" or event["type"] == "customer.subscription.deleted":
            subscription_id = event["data"]["object"]["id"]
            stripe_service.sync_subscription_from_stripe(subscription_id)
        return {"status": "success"}
