from fastapi import APIRouter, Request
from app.database.models import Subscription
from app.payment.service import PaymentService
from app.payment.webhook import handle_stripe_webhook
from app.lib.dependency import DatabaseSession, AuthSession, TransactionSession
from app.payment.dto import (
    CheckoutSessionDto,
    CreateCheckoutSessionDto,
    CheckoutSession,
    CreatePortalSessionDto,
    PortalSession,
    UpdateSubscriptionRequest,
    CancelSubscriptionRequest,
)

router = APIRouter(tags=["payments"])


@router.post("/checkout", operation_id="createCheckoutSession", response_model=CheckoutSession)
async def create_checkout_session(data: CreateCheckoutSessionDto, session: TransactionSession, user_session: AuthSession):
    stripe_service = PaymentService(session)
    dto = CheckoutSessionDto(user_id=user_session.user.id, price_id=data.price_id, success_url=data.success_url, cancel_url=data.cancel_url)
    url = await stripe_service.create_checkout_session(dto)
    return CheckoutSession(url=url)


@router.post("/portal", operation_id="createPortalSession", response_model=PortalSession)
async def create_portal_session(data: CreatePortalSessionDto, session: TransactionSession, user_session: AuthSession):
    stripe_service = PaymentService(session)
    url = await stripe_service.create_portal_session(user_session.user.id, data.return_url)
    return PortalSession(url=url)


@router.get("/subscription", operation_id="getSubscription", response_model=Subscription | None)
async def get_subscription(session: DatabaseSession, user_session: AuthSession):
    stripe_service = PaymentService(session)
    subscription = await stripe_service.get_subscription(user_session.user.id)
    if not subscription: return None
    return subscription


@router.put("/subscription", operation_id="updateSubscription", response_model=Subscription)
async def update_subscription(data: UpdateSubscriptionRequest, session: TransactionSession, user_session: AuthSession):
    stripe_service = PaymentService(session)
    subscription = await stripe_service.update_subscription(user_session.user.id, data.price_id)
    return subscription


@router.post("/subscription/cancel", operation_id="cancelSubscription", response_model=Subscription)
async def cancel_subscription(data: CancelSubscriptionRequest, session: TransactionSession, user_session: AuthSession):
    stripe_service = PaymentService(session)
    subscription = await stripe_service.cancel_subscription(user_session.user.id, data.cancel_immediately)
    return subscription


@router.post("/webhook", operation_id="stripeWebhook")
async def stripe_webhook(request: Request, session: TransactionSession):
    return await handle_stripe_webhook(request, session)
