from fastapi import HTTPException, Request
from app.config import settings
from app.database import Database
from app.auth.service import AuthService


async def auth_guard(request: Request) -> None:
    endpoint = request.scope.get("endpoint")
    if request.method == "OPTIONS": return
    if endpoint and getattr(endpoint, "is_public", False): return

    token = request.cookies.get(settings.cookie_key)
    if not token: raise HTTPException(status_code=401, detail="Unauthorized")

    async with Database.async_session() as db:
        auth_service = AuthService(db)
        try: payload = auth_service.verify_jwt_token(token)
        except Exception: raise HTTPException(status_code=401, detail="Unauthorized")
        setattr(request.state, "user", payload.user)
        setattr(request.state, "session", payload.session)
