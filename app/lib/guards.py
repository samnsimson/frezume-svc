from uuid import UUID
from fastapi import HTTPException, Request
from app.database import Database
from app.database.models import Usage, User, Session, Plan, Subscription
from sqlmodel.ext.asyncio.session import AsyncSession
from app.subscription.service import SubscriptionService
from app.usage.service import UsageService


async def usage_guard(request: Request) -> Usage:
    user: User | None = getattr(request.state, "user", None)
    session: Session | None = getattr(request.state, "session", None)
    if not user or not session: raise HTTPException(status_code=401, detail="Unauthorized")

    async def _get_subscription(user_id: UUID, db: AsyncSession) -> Subscription:
        subscription_service = SubscriptionService(db)
        subscription = await subscription_service.get_by_user_id(user_id)
        if not subscription: raise HTTPException(status_code=403, detail="Subscription not found. Please contact support.")
        return subscription

    async def _get_usage(user_id: UUID, db: AsyncSession) -> Usage:
        usage_service = UsageService(db)
        usage = await usage_service.get_usage(user_id)
        if not usage: return await usage_service.create_usage(user_id)
        return usage

    async with Database.async_session() as db:
        subscription = await _get_subscription(user.id, db)
        usage = await _get_usage(user.id, db)
        if subscription.plan == Plan.FREE and usage.rewrites >= 5: raise HTTPException(status_code=403, detail="Usage limit exceeded")
        return usage
