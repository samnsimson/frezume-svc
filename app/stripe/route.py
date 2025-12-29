from fastapi import APIRouter, Request
from app.stripe.service import StripeService
from app.stripe.webhook import handle_stripe_webhook
from app.stripe.dto import (
    CreateCheckoutSessionDto,
    CheckoutSession,
    CreatePortalSessionDto,
    PortalSession,
)
from app.lib.dependency import AuthSession, TransactionSession

router = APIRouter(tags=["stripe"])


@router.post("/checkout", operation_id="createCheckoutSession", response_model=CheckoutSession)
async def create_checkout_session(data: CreateCheckoutSessionDto, session: TransactionSession, user_session: AuthSession):
    from app.stripe.dto import CheckoutSessionDto
    from app.subscription.service import SubscriptionService
    stripe_service = StripeService(session)
    subscription_service = SubscriptionService(session)
    subscription = await subscription_service.get_by_user_id(user_session.user.id)
    dto = CheckoutSessionDto(user_id=user_session.user.id, price_id=data.price_id, success_url=data.success_url, cancel_url=data.cancel_url)
    url = await stripe_service.create_checkout_session(dto, subscription)
    return CheckoutSession(url=url)


@router.post("/portal", operation_id="createPortalSession", response_model=PortalSession)
async def create_portal_session(data: CreatePortalSessionDto, session: TransactionSession, user_session: AuthSession):
    stripe_service = StripeService(session)
    url = await stripe_service.create_portal_session(user_session.user.id, data.return_url)
    return PortalSession(url=url)


@router.post("/webhook", operation_id="stripeWebhook")
async def stripe_webhook(request: Request, session: TransactionSession):
    return await handle_stripe_webhook(request, session)
