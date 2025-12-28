from fastapi import Request
from fastapi.responses import JSONResponse
from sqlmodel import Session
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import Database
from app.auth.service import AuthService
from app.session.service import SessionService
from app.user.service import UserService


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS": return await call_next(request)
            if self.should_skip_path(request.url.path): return await call_next(request)
            token, from_cookie = self.extract_token(request)
            if not token: return self.create_unauthorized_response(clear_cookie=from_cookie)
            with Session(Database.engine) as db_session:
                user_data, session_data, error = self.authenticate_user(token, db_session)
                if error: return self.create_unauthorized_response(detail=error, clear_cookie=from_cookie)
                setattr(request.state, "user", user_data)
                setattr(request.state, "session", session_data)
        except Exception as e:
            error_detail = str(e) if str(e) else "Unauthorized"
            return self.create_unauthorized_response(detail=error_detail, clear_cookie=from_cookie)
        return await call_next(request)

    def should_skip_path(self, path: str) -> bool:
        skip_paths = ["/api/docs", "/api/redoc", "/api/openapi.json", "/api/favicon.ico"]
        return path in skip_paths or path.startswith("/api/auth/") or path.startswith("/api/stripe/webhook")

    def extract_token(self, request: Request) -> tuple[str | None, bool]:
        cookie_token = request.cookies.get("resumevx:auth")
        auth_header = request.headers.get("Authorization")
        if cookie_token: return cookie_token, True
        if auth_header and auth_header.startswith("Bearer "): return auth_header.replace("Bearer ", ""), False
        return None, False

    def create_unauthorized_response(self, detail: str = "Unauthorized", status_code: int = 401, clear_cookie: bool = False) -> JSONResponse:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        if clear_cookie: response.delete_cookie(key="resumevx:auth")
        return response

    def authenticate_user(self, token: str, db_session: Session) -> tuple:
        auth_service = AuthService(db_session)
        user_service = UserService(db_session)
        session_service = SessionService(db_session)
        try: payload = auth_service.verify_jwt_token(token)
        except Exception: return None, None, "Invalid or expired token"
        user_data = user_service.get_user(payload.user.id)
        session_data = session_service.get_session_by_token(payload.session.session_token)
        if session_data.session_token != payload.session.session_token: return None, None, "Invalid session token"
        return user_data, session_data, None
