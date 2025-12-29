from fastapi import APIRouter
from app.database.models import Subscription
from app.subscription.service import SubscriptionService
from app.subscription.dto import UpdateSubscriptionRequest, CancelSubscriptionRequest
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
