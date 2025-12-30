from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import Database
from app.database.models import Plan, User
from app.subscription.service import SubscriptionService
from app.usage.service import UsageService


class UsageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS": return await call_next(request)
            if not self.should_check_usage(request.url.path): return await call_next(request)
            user: User | None = getattr(request.state, "user", None)
            if not user: return JSONResponse(status_code=401, content={"detail": "Authentication required to use this endpoint"})

            async with Database.async_session() as db:
                usage_service = UsageService(db)
                subscription_service = SubscriptionService(db)
                subscription = await subscription_service.get_by_user_id(user.id)
                if not subscription: return JSONResponse(status_code=403, content={"detail": "Subscription not found. Please contact support."})
                if subscription.plan not in [Plan.FREE]: return await call_next(request)
                usage = await usage_service.get_usage(user.id)
                rewrites = usage.rewrites if usage else 0
                if rewrites > 5: return JSONResponse(status_code=403, content={"detail": "You have exceeded the maximum number of rewrites (5) for the free plan. Please upgrade to continue.", "rewrites_used": rewrites, "rewrites_limit": 5})
                return await call_next(request)
        except Exception as e:
            return JSONResponse(status_code=400, content={"detail": f"Error checking usage limits: {str(e)}"})

    def should_check_usage(self, path: str) -> bool:
        return path == "/api/document/rewrite"
