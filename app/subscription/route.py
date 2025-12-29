from fastapi import APIRouter, Request
from app.database.models import Subscription
from app.subscription.service import SubscriptionService
from app.subscription.dto import UpdateSubscriptionRequest, CancelSubscriptionRequest, CreateCheckoutSessionDto, CheckoutSession, CreatePortalSessionDto, PortalSession
from app.subscription.webhook import handle_stripe_webhook
from app.lib.dependency import DatabaseSession, AuthSession, TransactionSession

router = APIRouter(tags=["subscriptions"])


@router.get("/subscription", operation_id="getSubscription", response_model=Subscription | None)
async def get_by_user_id(session: DatabaseSession, user_session: AuthSession):
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_user_id(user_session.user.id)
    if not subscription: return None
    return subscription


@router.put("/subscription", operation_id="updateSubscription", response_model=Subscription)
async def update_subscription(data: UpdateSubscriptionRequest, session: TransactionSession, user_session: AuthSession):
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.update_subscription_plan(user_session.user.id, data.price_id)
    return subscription


@router.post("/subscription/cancel", operation_id="cancelSubscription", response_model=Subscription)
async def cancel_subscription(data: CancelSubscriptionRequest, session: TransactionSession, user_session: AuthSession):
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.cancel_subscription(user_session.user.id, data.cancel_immediately)
    return subscription


@router.post("/checkout", operation_id="createCheckoutSession", response_model=CheckoutSession)
async def create_checkout_session(data: CreateCheckoutSessionDto, session: TransactionSession, user_session: AuthSession):
    subscription_service = SubscriptionService(session)
    url = await subscription_service.create_checkout_session(user_session.user, data.price_id, data.success_url, data.cancel_url)
    return CheckoutSession(url=url)


@router.post("/portal", operation_id="createPortalSession", response_model=PortalSession)
async def create_portal_session(data: CreatePortalSessionDto, session: TransactionSession, user_session: AuthSession):
    subscription_service = SubscriptionService(session)
    url = await subscription_service.create_portal_session(user_session.user, data.return_url)
    return PortalSession(url=url)


@router.post("/webhook", operation_id="stripeWebhook")
async def stripe_webhook(request: Request, session: TransactionSession):
    return await handle_stripe_webhook(request, session)
