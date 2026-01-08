import re
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import Database
from app.auth.service import AuthService
from app.session.service import SessionService
from app.user.service import UserService
from typing import Set, Pattern
from app.config import settings
from app.lib.constants import (
    ERROR_UNAUTHORIZED,
    ERROR_INVALID_OR_EXPIRED_TOKEN,
    ERROR_USER_OR_SESSION_NOT_FOUND,
    ERROR_INVALID_SESSION_TOKEN,
)


class AuthMiddleware(BaseHTTPMiddleware):
    logger = logging.getLogger(__name__)
    _exact_skip_paths: Set[str] = {"/docs", "/redoc", "/openapi.json", "/favicon.ico"}
    _require_auth_paths: Set[str] = {"/auth/account", "/auth/get-session", "/auth/verify-email", "/auth/resend-verification-email"}
    _prefix_skip_paths: Set[str] = {"/subscriptions/webhook", "/static", "/docs"}
    _regex_skip_patterns: Set[Pattern] = {re.compile(r"^/auth/(?!account$|get-session$|verify-email$|resend-verification-email$).*$")}

    def _log_request(self, request: Request):
        """Logs the request"""
        self.logger.info(f"\n=== Request: {request.method} {request.url.path} ===")
        self.logger.info(f"Client IP: {request.client.host}")
        self.logger.info(f"Should skip: {self.should_skip_path(request.url.path)}")

    async def dispatch(self, request: Request, call_next):
        """Dispatches the request and authenticates the user"""
        self._log_request(request)
        if request.method == "OPTIONS": return await call_next(request)
        if self.should_skip_path(request.url.path): return await call_next(request)
        token, from_cookie = self.extract_token(request)
        if not token: return self.create_unauthorized_response(clear_cookie=from_cookie)
        async with Database.async_session() as db_session:
            user_data, session_data, error = await self.authenticate_user(token, db_session)
            if error: return self.create_unauthorized_response(detail=error, clear_cookie=from_cookie)
            setattr(request.state, "user", user_data)
            setattr(request.state, "session", session_data)
        return await call_next(request)

    def should_skip_path(self, path: str) -> bool:
        """Returns True if auth should be skipped for this path"""
        if path in self._require_auth_paths: return False
        if path in self._exact_skip_paths: return True
        if any(path.startswith(prefix) for prefix in self._prefix_skip_paths): return True
        if any(pattern.match(path) for pattern in self._regex_skip_patterns): return True
        return False

    def extract_token(self, request: Request) -> tuple[str | None, bool]:
        """Extracts the token from the request"""
        cookie_token = request.cookies.get(settings.cookie_key)
        auth_header = request.headers.get("Authorization")
        if cookie_token: return cookie_token, True
        if auth_header and auth_header.startswith("Bearer "): return auth_header.replace("Bearer ", ""), False
        return None, False

    def create_unauthorized_response(self, detail: str = ERROR_UNAUTHORIZED, status_code: int = 401, clear_cookie: bool = False) -> JSONResponse:
        """Creates a JSON response for unauthorized requests"""
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        if clear_cookie: response.delete_cookie(key=settings.cookie_key)
        return response

    async def authenticate_user(self, token: str, db_session) -> tuple:
        """Authenticates the user and returns the user and session data"""
        auth_service = AuthService(db_session)
        user_service = UserService(db_session)
        session_service = SessionService(db_session)
        try: payload = auth_service.verify_jwt_token(token)
        except Exception: return None, None, ERROR_INVALID_OR_EXPIRED_TOKEN
        user_data = await user_service.get_user(payload.user.id)
        session_data = await session_service.get_session_by_token(payload.session.session_token)
        if not user_data or not session_data: return None, None, ERROR_USER_OR_SESSION_NOT_FOUND
        if session_data.session_token != payload.session.session_token: return None, None, ERROR_INVALID_SESSION_TOKEN
        return user_data, session_data, None
