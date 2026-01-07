import logging
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)
        response = await call_next(request)
        log_data = {
            "timestamp": start_time.isoformat(),
            "method": request.method,
            "url": str(request.url),
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "country": request.headers.get("CF-IPCountry"),
            "status": response.status_code,
            "duration": (datetime.now(timezone.utc) - start_time).total_seconds()
        }
        self.logger.info(log_data)
        return response
